"""Online-only Field Operations inspection API.

Every mutation uses the existing Service Vehicle Inspection DocType and its
validation. No second workflow, bypass of permissions, or cached private data.
"""

import frappe
from frappe import _

INSPECTION = "Service Vehicle Inspection"
JOB_CARD = "Service Job Card"
TEMPLATE = "Service Pre Inspection Template"
STAGES = ("Pre-Service", "Post-Service")
DRAFT_FIELDS = (
	"inspection_remarks",
	"driver_name",
	"vehicle_plate_number",
	"date",
	"mileage",
	"gps_latitude",
	"gps_longitude",
	"gps_accuracy",
	"gps_captured_at",
	"image_upload",
)


def _require_stage(stage):
	if stage not in STAGES:
		frappe.throw(_("Select Pre-Service or Post-Service."))


def _read_card(name):
	card = frappe.get_doc(JOB_CARD, name)
	card.check_permission("read")
	return card


def _inspection(name, *, write=False):
	doc = frappe.get_doc(INSPECTION, name, for_update=write)
	doc.check_permission("write" if write else "read")
	_read_card(doc.service_job_card)
	return doc


def prevent_private_cache(response, request):
	if request.path in ("/field", "/field-login") or request.path.startswith(
		("/api/method/servicems.field_api.", "/private/files/")
	):
		response.headers["Cache-Control"] = "no-store, private, max-age=0"
		response.headers["Pragma"] = "no-cache"


@frappe.whitelist()
def get_field_jobs(limit=40):
	"""Return only Job Cards visible under normal Frappe permissions."""
	limit = min(max(int(limit), 1), 100)
	jobs = frappe.get_list(
		JOB_CARD,
		fields=[
			"name",
			"status",
			"service_item_name",
			"vehicle_model",
			"workshop",
			"customer",
			"modified",
		],
		order_by="modified desc",
		page_length=limit,
	)
	return jobs


@frappe.whitelist()
def get_field_job(job_card):
	card = _read_card(job_card)
	return {
		"name": card.name,
		"status": card.status,
		"service_item_name": card.service_item_name,
		"vehicle_model": card.vehicle_model,
		"workshop": card.workshop,
		"customer": card.customer,
	}


@frappe.whitelist()
def get_job_inspections(job_card):
	_read_card(job_card)
	return frappe.get_list(
		INSPECTION,
		filters={"service_job_card": job_card},
		fields=[
			"name",
			"inspection_stage",
			"inspection_status",
			"inspection_template",
			"inspected_on",
			"completed_by",
			"corrects_inspection",
			"modified",
		],
		order_by="modified desc",
		page_length=100,
	)


@frappe.whitelist()
def get_inspection_templates(stage):
	_require_stage(stage)
	rows = frappe.get_list(
		TEMPLATE,
		fields=["name", "template_name", "applicable_stage", "require_photographs"],
		page_length=200,
	)
	return [row for row in rows if not row.applicable_stage or row.applicable_stage == stage]


@frappe.whitelist()
def get_field_inspection(name):
	inspection = _inspection(name)
	return inspection.as_dict()


@frappe.whitelist()
def get_inspection_photos(name):
	from servicems.inspection_files import evidence_inspections

	doc = _inspection(name)
	names = list(evidence_inspections(doc))
	photos = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": INSPECTION,
			"attached_to_name": ["in", names],
			"is_private": 1,
			"is_folder": 0,
		},
		fields=["name", "file_name", "file_url", "attached_to_name"],
		order_by="creation asc",
		limit_page_length=100,
	)
	unique = {}
	for photo in photos:
		owner = photo.pop("attached_to_name")
		photo.can_delete = doc.inspection_status == "Draft" and owner == doc.name
		unique.setdefault(photo.file_url, photo)
	return list(unique.values())


@frappe.whitelist(methods=["POST"])
def upload_inspection_photo(name):
	from frappe.utils.file_manager import get_content_hash

	from servicems.inspection_files import validate_image

	doc = _inspection(name, write=True)
	if doc.inspection_status != "Draft":
		frappe.throw(_("Completed inspections cannot receive new photographs."))
	photo = frappe.request.files.get("file")
	if not photo:
		frappe.throw(_("Select a photograph to upload."))
	content = photo.stream.read(10 * 1024 * 1024 + 1)
	if len(content) > 10 * 1024 * 1024:
		frappe.throw(_("Photographs must be 10 MB or smaller."))
	validate_image(content)
	existing = frappe.db.get_value(
		"File",
		{
			"attached_to_doctype": INSPECTION,
			"attached_to_name": doc.name,
			"is_private": 1,
			"content_hash": get_content_hash(content),
		},
		["name", "file_url", "file_name", "is_private"],
		as_dict=True,
	)
	if existing:
		return existing
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": photo.filename,
			"content": content,
			"attached_to_doctype": INSPECTION,
			"attached_to_name": doc.name,
			"is_private": 1,
		}
	).insert(ignore_permissions=True)
	return {
		"name": file.name,
		"file_url": file.file_url,
		"file_name": file.file_name,
		"is_private": file.is_private,
	}


@frappe.whitelist(methods=["POST"])
def start_inspection(job_card, stage, template):
	_require_stage(stage)
	_read_card(job_card)
	frappe.has_permission(INSPECTION, "create", throw=True)
	template_doc = frappe.get_doc(TEMPLATE, template)
	template_doc.check_permission("read")
	if template_doc.applicable_stage and template_doc.applicable_stage != stage:
		frappe.throw(_("This template is not configured for the selected stage."))
	doc = frappe.get_doc(
		{
			"doctype": INSPECTION,
			"service_job_card": job_card,
			"inspection_stage": stage,
			"inspection_template": template,
			"inspection_status": "Draft",
		}
	)
	doc.insert()
	return {"name": doc.name, "inspection_status": doc.inspection_status}


def _draft_values(values):
	if isinstance(values, str):
		values = frappe.parse_json(values)
	if not isinstance(values, dict):
		frappe.throw(_("Expected draft fields."))
	allowed = set(DRAFT_FIELDS)
	if set(values) - allowed:
		frappe.throw(_("Some draft fields cannot be edited from the Field PWA."))
	if isinstance(values.get("gps_captured_at"), str) and values["gps_captured_at"].endswith("Z"):
		from frappe.utils import convert_utc_to_system_timezone, get_datetime

		values["gps_captured_at"] = convert_utc_to_system_timezone(
			get_datetime(values["gps_captured_at"])
		).replace(tzinfo=None)
	return values


def _apply_answers(doc, answers):
	if isinstance(answers, str):
		answers = frappe.parse_json(answers)
	if not isinstance(answers, list):
		frappe.throw(_("Checklist answers must be a list."))
	by_name = {row.name: row for row in doc.checklist}
	if len(answers) != len({row.get("name") for row in answers if isinstance(row, dict)}):
		frappe.throw(_("Duplicate checklist row."))
	for answer in answers:
		if not isinstance(answer, dict) or set(answer) - {"name", "answer", "remarks", "photograph"}:
			frappe.throw(_("Invalid checklist answer."))
		if answer.get("name") not in by_name:
			frappe.throw(_("Checklist item does not belong to this inspection."))
		row = by_name[answer["name"]]
		for field in ("answer", "remarks", "photograph"):
			if field in answer:
				row.set(field, answer[field])


def _edit_draft(doc, values, answers, expected_modified):
	if expected_modified and frappe.utils.get_datetime(expected_modified) != frappe.utils.get_datetime(
		doc.modified
	):
		frappe.throw(
			_("This inspection changed in another session. Reopen it before saving."),
			frappe.TimestampMismatchError,
		)
	if doc.inspection_status != "Draft":
		frappe.throw(_("Completed inspections cannot be edited. Create a correction."))
	for key, value in _draft_values(values or {}).items():
		doc.set(key, value)
	if answers is not None:
		_apply_answers(doc, answers)


@frappe.whitelist(methods=["POST"])
def save_field_draft(name, values=None, answers=None, expected_modified=None):
	doc = _inspection(name, write=True)
	_edit_draft(doc, values, answers, expected_modified)
	doc.save()
	return {"name": doc.name, "inspection_status": doc.inspection_status, "modified": str(doc.modified)}


@frappe.whitelist(methods=["POST"])
def delete_inspection_photo(name, file_name, values=None, answers=None, expected_modified=None):
	from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
		protect_completed_photo,
	)

	doc = _inspection(name, write=True)
	photo = frappe.get_doc("File", file_name, for_update=True)
	if (
		photo.attached_to_doctype != INSPECTION
		or photo.attached_to_name != doc.name
		or not photo.is_private
		or photo.is_folder
	):
		frappe.throw(_("Only photographs uploaded to this draft can be deleted."), frappe.PermissionError)
	protect_completed_photo(photo)
	_edit_draft(doc, values, answers, expected_modified)
	if doc.image_upload == photo.file_url:
		doc.image_upload = ""
	for row in doc.checklist:
		if row.photograph == photo.file_url:
			row.photograph = ""
	doc.save()
	# Parent write access and exact attachment ownership were checked above.
	photo.delete(ignore_permissions=True)
	return {"name": doc.name, "modified": str(doc.modified), "deleted_url": photo.file_url}


@frappe.whitelist(methods=["POST"])
def complete_field_inspection(name):
	doc = _inspection(name, write=True)
	if doc.inspection_status != "Draft":
		frappe.throw(_("This inspection is already completed."))
	doc.inspection_status = "Completed"
	doc.save()
	return {"name": doc.name, "inspection_status": doc.inspection_status}


@frappe.whitelist(methods=["POST"])
def create_field_correction(name, reason):
	doc = _inspection(name, write=True)
	return {"name": doc.create_correction(reason)}
