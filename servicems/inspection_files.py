"""Protect physical inspection evidence before Frappe deletes a File."""

from io import BytesIO

import frappe
from frappe import _
from PIL import Image, UnidentifiedImageError

INSPECTION = "Service Vehicle Inspection"


def validate_image(content):
	try:
		with Image.open(BytesIO(content)) as image:
			if image.format not in ("JPEG", "PNG", "WEBP", "GIF") or image.width * image.height > 40_000_000:
				frappe.throw(_("Use a JPEG, PNG, WebP or GIF photograph up to 40 megapixels."))
			image.load()
	except (UnidentifiedImageError, OSError, ValueError):
		frappe.throw(_("Upload a valid JPEG, PNG, WebP or GIF photograph."), exc=frappe.ValidationError)


def evidence_inspections(doc):
	"""Only this inspection and its protected correction ancestry own its evidence."""
	names = {doc.name}
	source_name = doc.corrects_inspection
	while source_name:
		if source_name in names or len(names) > 50:
			frappe.throw(_("Invalid inspection correction history."))
		source = frappe.get_doc(INSPECTION, source_name)
		source.check_permission("read")
		if source.service_job_card != doc.service_job_card or source.inspection_stage != doc.inspection_stage:
			frappe.throw(_("Photographs must belong to the same inspection history."))
		names.add(source.name)
		source_name = source.corrects_inspection
	return names


def validate_inspection_file(doc, method=None, *, check_content=True):
	from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
		protect_completed_photo,
	)

	protect_completed_photo(doc)
	if doc.attached_to_doctype != INSPECTION:
		return
	inspection = frappe.get_doc(INSPECTION, doc.attached_to_name, for_update=True)
	inspection.check_permission("write")
	from servicems.inspection_workflow import validate_inspection

	validate_inspection(inspection)
	if inspection.inspection_status != "Draft":
		frappe.throw(_("Completed inspections cannot receive or change photographs."))
	if not doc.is_private or (doc.file_url and not doc.file_url.startswith("/private/files/")):
		frappe.throw(_("Inspection photographs must be private local uploads."))
	if check_content and (doc.is_new() or doc.has_value_changed("file_url")):
		validate_image(doc.get_content(encodings=[]))


class InspectionEvidenceMixin:
	def get_content(self, encodings=None):
		if self.attached_to_doctype == INSPECTION and encodings is None:
			encodings = []
		return super().get_content(encodings=encodings)

	def is_downloadable(self):
		from servicems.field_permissions import file_permission

		return file_permission(self, ptype="read") and super().is_downloadable()

	def before_insert(self):
		validate_inspection_file(self, check_content=False)
		return super().before_insert()

	def on_trash(self):
		from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
			protect_completed_photo,
		)

		protect_completed_photo(self)
		return super().on_trash()
