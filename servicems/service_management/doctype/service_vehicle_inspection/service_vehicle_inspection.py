# Copyright (c) 2022, Aakvatech Limited and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class ServiceVehicleInspection(Document):
	def validate(self):
		previous = None
		if not self.is_new():
			frappe.db.sql(
				"select name from `tabService Vehicle Inspection` where name=%s for update", self.name
			)
			previous = frappe.get_doc(self.doctype, self.name)
			if previous.inspection_status == "Completed":
				frappe.throw(_("Completed inspections are immutable. Create a correction with a reason."))
		if self.service_job_card:
			frappe.get_doc("Service Job Card", self.service_job_card).check_permission("read")
		if self.corrects_inspection:
			source = frappe.get_doc(self.doctype, self.corrects_inspection)
			source.check_permission("read")
			if (
				source.inspection_status != "Completed"
				or source.service_job_card != self.service_job_card
				or source.inspection_stage != self.inspection_stage
				or not self.correction_reason
			):
				frappe.throw(
					_(
						"A correction requires a completed inspection for the same Job Card and stage, and a reason."
					)
				)
		if self.inspection_stage not in ("Pre-Service", "Post-Service", None, ""):
			frappe.throw(_("Invalid inspection stage."))
		if self.is_new():
			if not self.inspection_template:
				frappe.throw(_("Select an inspection template before creating a new inspection."))
			self.template_snapshot = source.template_snapshot if self.corrects_inspection else None
			if self.corrects_inspection:
				self.require_photographs_snapshot = source.require_photographs_snapshot
				self.require_gps_snapshot = source.require_gps_snapshot
		if previous and previous.template_snapshot:
			for field in (
				"service_job_card",
				"inspection_stage",
				"inspection_template",
				"corrects_inspection",
				"legacy_job_card",
			):
				if self.get(field) != previous.get(field):
					frappe.throw(_("Inspection Job Card, stage, template and correction source are fixed."))
		if (
			self.inspection_template
			and not (previous and previous.template_snapshot)
			and not self.corrects_inspection
		):
			template = frappe.get_doc("Service Pre Inspection Template", self.inspection_template)
			template.check_permission("read")
			if template.applicable_stage and template.applicable_stage != self.inspection_stage:
				frappe.throw(_("Selected template does not apply to this inspection stage."))
			if not self.corrects_inspection:
				self.require_photographs_snapshot = int(bool(template.require_photographs))
				self.require_gps_snapshot = int(bool(template.require_gps))
		if self.inspection_status == "Completed" and not self.inspection_stage:
			frappe.throw(_("Select an inspection stage."))
		if (
			previous
			and previous.inspection_template != self.inspection_template
			and (previous.checklist or previous.template_snapshot)
		):
			frappe.throw(
				_("Create a new inspection to use a different template; recorded answers are preserved.")
			)
		if previous and previous.template_snapshot:
			self.template_snapshot = previous.template_snapshot
			self.require_photographs_snapshot = previous.require_photographs_snapshot
			self.require_gps_snapshot = previous.require_gps_snapshot
			baseline = frappe.parse_json(previous.template_snapshot)
			if len(self.checklist) != len(baseline) or any(
				row.inspection_item != item.get("inspection_item")
				for row, item in zip(self.checklist, baseline, strict=True)
			):
				frappe.throw(
					_("Recorded checklist items are fixed; create a new inspection to change the checklist.")
				)
			for row, item in zip(self.checklist, baseline, strict=True):
				for field in ("inspection_type", "option", "require_photo", "is_required"):
					row.set(
						field, item.get(field) or (0 if field in ("require_photo", "is_required") else "")
					)
		if self.inspection_template and not self.template_snapshot:
			template = frappe.get_doc("Service Pre Inspection Template", self.inspection_template)
			template.check_permission("read")
			if template.applicable_stage and template.applicable_stage != self.inspection_stage:
				frappe.throw(_("Selected template does not apply to this inspection stage."))
			if not previous:
				self.require_photographs_snapshot = int(bool(template.require_photographs))
				self.require_gps_snapshot = int(bool(template.require_gps))
			if self.checklist:
				if len(self.checklist) != len(template.pre_inspection_items) or any(
					row.inspection_item != spec.inspection_item
					for row, spec in zip(self.checklist, template.pre_inspection_items, strict=True)
				):
					frappe.throw(_("Checklist items must match the selected template."))
				for row, spec in zip(self.checklist, template.pre_inspection_items, strict=True):
					row.require_photo = spec.require_photo
					row.is_required = spec.is_required
			else:
				for row in template.pre_inspection_items:
					self.append(
						"checklist",
						{
							field: row.get(field)
							for field in (
								"inspection_item",
								"inspection_type",
								"option",
								"require_photo",
								"is_required",
							)
						},
					)
			self.template_snapshot = frappe.as_json([row.as_dict() for row in self.checklist])
		if self.is_new() and self.corrects_inspection and self.template_snapshot:
			baseline = frappe.parse_json(self.template_snapshot)
			if self.inspection_template != source.inspection_template or len(self.checklist) != len(baseline):
				frappe.throw(_("Corrections must preserve the source template and checklist."))
			for row, item in zip(self.checklist, baseline, strict=True):
				for field in ("inspection_item", "inspection_type", "option", "require_photo", "is_required"):
					row.set(field, item.get(field))
		self.validate_gps()
		photo_urls = [url for url in [self.image_upload, *[row.photograph for row in self.checklist]] if url]
		self.validate_photographs(photo_urls)
		if self.inspection_status != "Completed":
			self.completed_by = previous.completed_by if previous else None
			self.inspected_on = previous.inspected_on if previous else None
			return
		if not self.service_job_card or not self.inspection_stage:
			frappe.throw(_("A completed inspection requires a Job Card and inspection stage."))
		if not self.inspection_template:
			frappe.throw(_("Select an inspection template before completion."))
		attached = bool(photo_urls)
		if not attached and not self.is_new():
			attached = bool(
				frappe.db.exists(
					"File",
					{
						"attached_to_doctype": self.doctype,
						"attached_to_name": self.name,
						"is_folder": 0,
						"is_private": 1,
						"file_type": ["in", ["JPG", "JPEG", "PNG", "WEBP", "GIF"]],
					},
				)
			)
		if self.require_photographs_snapshot and not attached:
			frappe.throw(_("Attach at least one inspection photograph before completion."))
		for row in self.checklist:
			if row.is_required and not str(row.answer or "").strip():
				frappe.throw(_("Answer required for inspection item {0}.").format(row.inspection_item))
			if row.require_photo and not row.photograph:
				frappe.throw(
					_("A photograph is required for inspection item {0}.").format(row.inspection_item)
				)
		if self.require_gps_snapshot and (
			self.gps_latitude is None
			or self.gps_longitude is None
			or not self.gps_captured_at
			or self.gps_accuracy is None
		):
			frappe.throw(_("This template requires a GPS location capture before completion."))
		self.completed_by = frappe.session.user
		self.inspected_on = now()

	def validate_gps(self):
		if (self.gps_latitude is None) != (self.gps_longitude is None):
			frappe.throw(_("Capture latitude and longitude together."))
		for field, minimum, maximum in (
			("gps_latitude", -90, 90),
			("gps_longitude", -180, 180),
			("gps_accuracy", 0, float("inf")),
		):
			value = self.get(field)
			if value is not None and (
				not math.isfinite(float(value)) or not minimum <= float(value) <= maximum
			):
				frappe.throw(_("Invalid GPS coordinates or location accuracy."))

	def validate_photographs(self, urls):
		if not urls:
			return
		from servicems.inspection_files import evidence_inspections

		parents = list(evidence_inspections(self))
		for url in urls:
			photo = frappe.db.get_value(
				"File",
				{
					"file_url": url,
					"is_private": 1,
					"is_folder": 0,
					"attached_to_doctype": self.doctype,
					"attached_to_name": ["in", parents],
					"file_type": ["in", ["JPG", "JPEG", "PNG", "WEBP", "GIF"]],
				},
				"name",
			)
			if not photo:
				frappe.throw(
					_(
						"Photographs must be private uploads belonging to this inspection or its correction history."
					)
				)
			frappe.get_doc("File", photo).check_permission("read")

	def on_trash(self):
		if self.inspection_status == "Completed":
			frappe.throw(_("Completed inspections must be retained for history."))

	@frappe.whitelist()
	def create_correction(self, reason):
		self.check_permission("write")
		if self.inspection_status != "Completed" or not reason or not reason.strip():
			frappe.throw(_("Select a completed inspection and provide a correction reason."))
		corrected = frappe.copy_doc(self)
		corrected.update(
			dict(
				inspection_status="Draft",
				corrects_inspection=self.name,
				correction_reason=reason,
				completed_by=None,
				inspected_on=None,
			)
		)
		corrected.insert()
		return corrected.name


@frappe.whitelist()
def migrate_legacy_acceptance(job_card):
	"""Explicit opt-in snapshot: legacy fields remain authoritative and untouched."""
	card = frappe.get_doc("Service Job Card", job_card)
	card.check_permission("write")
	frappe.db.sql("select name from `tabService Job Card` where name=%s for update", card.name)
	existing = frappe.db.get_value("Service Vehicle Inspection", {"legacy_job_card": card.name}, "name")
	if existing:
		return existing
	from servicems.inspection_migration import LEGACY_ACCEPTANCE_FIELDS

	template_name = "Legacy Job Card Acceptance"
	if not frappe.db.exists("Service Pre Inspection Template", template_name):
		template = frappe.new_doc("Service Pre Inspection Template")
		template.template_name = template_name
		for field in LEGACY_ACCEPTANCE_FIELDS:
			meta = card.meta.get_field(field)
			if meta:
				template.append(
					"pre_inspection_items",
					dict(inspection_item=meta.label, inspection_type="Data", option=meta.options),
				)
		template.insert()
	inspection = frappe.new_doc("Service Vehicle Inspection")
	inspection.update(
		dict(
			service_job_card=card.name,
			legacy_job_card=card.name,
			inspection_stage="Pre-Service",
			inspection_status="Draft",
			inspection_template=template_name,
		)
	)
	for field in LEGACY_ACCEPTANCE_FIELDS:
		meta = card.meta.get_field(field)
		if meta:
			inspection.append(
				"checklist",
				dict(
					inspection_item=meta.label,
					inspection_type="Data",
					answer=str(card.get(field)) if card.get(field) is not None else "",
				),
			)
	inspection.insert()
	return inspection.name


def protect_completed_photo(doc, method=None):
	previous = doc.get_doc_before_save()
	urls = {url for url in (doc.file_url, previous.file_url if previous else None) if url}
	parents = [(doc.attached_to_doctype, doc.attached_to_name)]
	if previous:
		parents.append((previous.attached_to_doctype, previous.attached_to_name))
	for doctype, name in sorted(set(parents), key=str):
		if doctype == "Service Vehicle Inspection" and name:
			status = frappe.db.get_value(doctype, name, "inspection_status", for_update=True)
			if status == "Completed":
				frappe.throw(
					_(
						"Photographs attached to completed inspections must be retained. Create a correction inspection."
					)
				)
	if (
		not doc.is_new()
		and urls
		and frappe.db.sql(
			"""select i.name from `tabService Vehicle Inspection` i
	 left join `tabPre Inspection Item` c on c.parent=i.name and c.parenttype='Service Vehicle Inspection'
	 where i.inspection_status='Completed' and (i.image_upload in %(urls)s or c.photograph in %(urls)s) limit 1 FOR UPDATE""",
			{"urls": tuple(urls)},
		)
	):
		frappe.throw(_("Photographs referenced by completed inspections must be retained."))
