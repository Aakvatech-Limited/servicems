"""Real-record Field API, assignment, snapshot and private-evidence regressions."""

from io import BytesIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import frappe
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.wrappers import Request

from servicems import field_api as api
from servicems.field_permissions import FIELD_ROLE


class TestFieldOperations(TestCase):
	def setUp(self):
		self.previous_user = frappe.session.user
		frappe.set_user("Administrator")
		frappe.db.savepoint("field_records")
		self.token = frappe.generate_hash(length=8)
		vehicle = frappe.get_all("Service Vehicle", fields=["name", "customer"], limit=1)[0]
		workshop = frappe.get_all("Service Workshop", pluck="name", limit=1)[0]
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "Field Service " + self.token,
				"item_name": "Field inspection service",
				"item_group": "All Item Groups",
				"stock_uom": "Nos",
				"is_stock_item": 0,
			}
		).insert()
		task = frappe.get_doc({"doctype": "Service Task", "task_name": "Field Task " + self.token}).insert()
		service = frappe.get_doc(
			{
				"doctype": "Service Template",
				"template_name": "Field Service " + self.token,
				"item": item.name,
				"tasks": [{"task_name": task.name}],
			}
		).insert()
		self.cards = [
			frappe.get_doc(
				{
					"doctype": "Service Job Card",
					"workshop": workshop,
					"customer": vehicle.customer,
					"service_item_name": vehicle.name,
					"receiving_datetime": frappe.utils.now(),
					"status": "Active",
					"complains": [{"description": "Field inspection test"}],
					"services": [{"service": service.name}],
				}
			).insert()
			for _ in range(2)
		]
		self.template = frappe.get_doc(
			{
				"doctype": api.TEMPLATE,
				"template_name": "Field test " + self.token,
				"require_photographs": 0,
				"require_gps": 0,
				"applicable_stage": "Pre-Service",
				"pre_inspection_items": [
					{
						"inspection_item": "Lights",
						"inspection_type": "Check",
						"is_required": 1,
						"option": "Pass\nFail\nN/A",
					}
				],
			}
		).insert()
		self.file_paths = []
		self.existing_urls = set(frappe.get_all("File", pluck="file_url"))

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="field_records")
		for path in self.file_paths:
			path.unlink(missing_ok=True)
		if getattr(self, "technician", None):
			frappe.clear_cache(user=self.technician)
		frappe.set_user(self.previous_user)

	def start(self, stage="Pre-Service", card=None):
		result = api.start_inspection((card or self.cards[0]).name, stage, self.template.name)
		return frappe.get_doc(api.INSPECTION, result["name"])

	def answer(self, doc, **values):
		api.save_field_draft(
			doc.name,
			values=values,
			answers=[{"name": doc.checklist[0].name, "answer": "Pass", "remarks": "Checked"}],
		)
		return doc.reload()

	def upload(self, doc):
		buffer = BytesIO()
		Image.new("RGB", (8, 8), (int(self.token[:2], 16), 100, 200)).save(buffer, format="PNG")
		request = Request.from_values(
			base_url="https://servicems2.aakvaerp.com",
			method="POST",
			data={"file": FileStorage(stream=BytesIO(buffer.getvalue()), filename=f"field-{self.token}.png")},
		)
		with patch.object(frappe.local, "request", request, create=True):
			photo = api.upload_inspection_photo(doc.name)
		file = frappe.get_doc("File", photo["name"])
		if file.file_url not in self.existing_urls:
			self.file_paths.append(Path(file.get_full_path()))
		return file

	def field_user(self):
		self.technician = "field-" + self.token + "@example.invalid"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": self.technician,
				"first_name": "Field Test",
				"send_welcome_email": 0,
				"roles": [{"role": FIELD_ROLE}],
			}
		).insert()
		self.todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": self.technician,
				"reference_type": api.JOB_CARD,
				"reference_name": self.cards[0].name,
				"description": "Field test assignment",
			}
		).insert()
		frappe.set_user(self.technician)

	def test_missing_and_wrong_stage_templates_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": api.INSPECTION, "service_job_card": self.cards[0].name}).insert()
		with self.assertRaises(frappe.ValidationError):
			self.start(stage="Post-Service")

	def test_frozen_template_settings_and_checklist_survive_template_edits(self):
		doc = self.start()
		self.template.require_photographs = 1
		self.template.require_gps = 1
		self.template.applicable_stage = "Post-Service"
		self.template.pre_inspection_items[0].inspection_item = "Changed"
		self.template.save()
		doc = self.answer(doc)
		api.complete_field_inspection(doc.name)
		doc.reload()
		self.assertEqual(doc.checklist[0].inspection_item, "Lights")
		self.assertEqual(doc.require_photographs_snapshot, 0)
		self.assertEqual(doc.require_gps_snapshot, 0)

	def test_required_answers_and_item_photographs(self):
		self.template.pre_inspection_items[0].require_photo = 1
		self.template.save()
		doc = self.start()
		with self.assertRaisesRegex(frappe.ValidationError, "Answer required"):
			api.complete_field_inspection(doc.name)
		self.answer(doc)
		with self.assertRaisesRegex(frappe.ValidationError, "photograph is required"):
			api.complete_field_inspection(doc.name)
		photo = self.upload(doc)
		api.save_field_draft(
			doc.name, answers=[{"name": doc.checklist[0].name, "photograph": photo.file_url}]
		)
		api.complete_field_inspection(doc.name)
		self.assertEqual(doc.reload().inspection_status, "Completed")

	def test_stage_photographs_optional_and_required(self):
		doc = self.answer(self.start())
		api.complete_field_inspection(doc.name)
		self.template.require_photographs = 1
		self.template.save()
		required = self.answer(self.start())
		with self.assertRaisesRegex(frappe.ValidationError, "at least one"):
			api.complete_field_inspection(required.name)
		self.upload(required)
		api.complete_field_inspection(required.name)

	def test_repeat_photo_upload_does_not_duplicate_gallery(self):
		doc = self.start()
		first = self.upload(doc)
		second = self.upload(doc)
		self.assertEqual(first.name, second.name)
		self.assertEqual(len(api.get_inspection_photos(doc.name)), 1)

	def test_draft_photo_deletion_saves_edits_and_clears_required_references(self):
		self.template.pre_inspection_items[0].require_photo = 1
		self.template.save()
		doc = self.start()
		photo = self.upload(doc)
		self.field_user()
		self.assertTrue(api.get_inspection_photos(doc.name)[0].can_delete)
		result = api.delete_inspection_photo(
			doc.name,
			photo.name,
			values={"inspection_remarks": "Keep these edits", "image_upload": photo.file_url},
			answers=[{"name": doc.checklist[0].name, "answer": "Pass", "photograph": photo.file_url}],
			expected_modified=str(doc.modified),
		)
		doc.reload()
		self.assertEqual(doc.inspection_remarks, "Keep these edits")
		self.assertEqual(doc.checklist[0].answer, "Pass")
		self.assertFalse(doc.image_upload)
		self.assertFalse(doc.checklist[0].photograph)
		self.assertEqual(result["modified"], str(doc.modified))
		self.assertFalse(frappe.db.exists("File", photo.name))
		self.assertEqual(api.get_inspection_photos(doc.name), [])
		with self.assertRaisesRegex(frappe.ValidationError, "photograph is required"):
			api.complete_field_inspection(doc.name)

	def test_photo_deletion_rejects_completed_and_inherited_evidence(self):
		doc = self.answer(self.start())
		photo = self.upload(doc)
		api.complete_field_inspection(doc.name)
		self.assertFalse(api.get_inspection_photos(doc.name)[0].can_delete)
		with self.assertRaises(frappe.ValidationError):
			api.delete_inspection_photo(doc.name, photo.name)
		correction = api.create_field_correction(doc.name, "Review evidence")["name"]
		self.assertFalse(api.get_inspection_photos(correction)[0].can_delete)
		with self.assertRaises(frappe.PermissionError):
			api.delete_inspection_photo(correction, photo.name)
		self.assertTrue(frappe.db.exists("File", photo.name))

	def test_photo_deletion_rejects_unassigned_card_and_foreign_attachment(self):
		own = self.start()
		foreign = self.start(card=self.cards[1])
		photo = self.upload(foreign)
		self.field_user()
		with self.assertRaises(frappe.PermissionError):
			api.delete_inspection_photo(foreign.name, photo.name)
		with self.assertRaises(frappe.PermissionError):
			api.delete_inspection_photo(own.name, photo.name)
		self.assertTrue(frappe.db.exists("File", photo.name))

	def test_photo_deletion_preserves_bytes_referenced_by_completed_inspection(self):
		source = self.start()
		protected = self.upload(source)
		self.answer(source, image_upload=protected.file_url)
		api.complete_field_inspection(source.name)
		draft = self.start()
		copy = self.upload(draft)
		self.assertEqual(copy.file_url, protected.file_url)
		with self.assertRaisesRegex(frappe.ValidationError, "must be retained"):
			api.delete_inspection_photo(draft.name, copy.name, values={"inspection_remarks": "Rejected"})
		self.assertTrue(frappe.db.exists("File", copy.name))
		self.assertTrue(frappe.db.exists("File", protected.name))
		self.assertFalse(draft.reload().inspection_remarks)

	def test_photo_deletion_rejects_stale_or_invalid_edits_without_removing_file(self):
		doc = self.start()
		photo = self.upload(doc)
		old_modified = str(doc.modified)
		self.answer(doc, inspection_remarks="Saved elsewhere")
		with self.assertRaises(frappe.TimestampMismatchError):
			api.delete_inspection_photo(doc.name, photo.name, expected_modified=old_modified)
		with self.assertRaises(frappe.ValidationError):
			api.delete_inspection_photo(doc.name, photo.name, values={"gps_accuracy": -1})
		self.assertTrue(frappe.db.exists("File", photo.name))
		self.assertEqual(doc.reload().inspection_remarks, "Saved elsewhere")

	def test_uploaded_bytes_can_match_inaccessible_private_evidence_without_granting_source_access(self):
		source = self.start(card=self.cards[1])
		original = self.upload(source)
		self.answer(source)
		api.complete_field_inspection(source.name)
		target = self.start()
		self.field_user()
		with self.assertRaises(frappe.PermissionError):
			api.get_field_inspection(source.name)
		copy = self.upload(target)
		self.assertNotEqual(copy.name, original.name)
		self.assertEqual(copy.attached_to_name, target.name)
		self.assertEqual(copy.content_hash, original.content_hash)
		self.assertTrue(copy.is_downloadable())
		self.assertFalse(original.is_downloadable())
		with self.assertRaises(frappe.PermissionError):
			api.get_inspection_photos(source.name)

	def test_gps_required_accuracy_and_draft_validation(self):
		self.template.require_gps = 1
		self.template.save()
		doc = self.answer(self.start())
		with self.assertRaisesRegex(frappe.ValidationError, "requires a GPS"):
			api.complete_field_inspection(doc.name)
		for values in ({"gps_latitude": 95}, {"gps_accuracy": -1}, {"gps_accuracy": float("nan")}):
			with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
				api.save_field_draft(doc.name, values=values)
		self.answer(
			doc,
			gps_latitude=-6.8,
			gps_longitude=39.2,
			gps_accuracy=7,
			gps_captured_at="2026-11-06T08:00:00.000Z",
		)
		api.complete_field_inspection(doc.name)
		self.assertEqual(doc.reload().gps_accuracy, 7)
		self.assertEqual(str(doc.gps_captured_at), "2026-11-06 11:00:00")

	def test_direct_api_cannot_change_snapshot_or_reparent_checklist(self):
		doc = self.start()
		with self.assertRaises(frappe.ValidationError):
			api.save_field_draft(doc.name, values={"require_photographs_snapshot": 0})
		with self.assertRaises(frappe.ValidationError):
			api.save_field_draft(doc.name, answers=[{"name": "another-inspection-row", "answer": "Pass"}])
		doc.inspection_stage = "Post-Service"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_structural_checklist_flags_cannot_be_forged(self):
		doc = self.start()
		doc.checklist[0].is_required = 0
		doc.checklist[0].inspection_type = "Data"
		doc.checklist[0].option = "Bypass"
		doc.save()
		self.assertEqual(doc.checklist[0].is_required, 1)
		self.assertEqual(doc.checklist[0].inspection_type, "Check")
		self.assertEqual(doc.checklist[0].option, "Pass\nFail\nN/A")

	def test_stale_draft_save_rejected_without_losing_answers(self):
		doc = self.start()
		previous = str(doc.modified)
		self.answer(doc, inspection_remarks="Saved elsewhere")
		with self.assertRaises(frappe.TimestampMismatchError):
			api.save_field_draft(doc.name, values={"inspection_remarks": "Stale"}, expected_modified=previous)
		self.assertEqual(doc.reload().inspection_remarks, "Saved elsewhere")

	def test_pre_and_post_completion_with_correction_history(self):
		for stage in ("Pre-Service", "Post-Service"):
			self.template.applicable_stage = stage
			self.template.save()
			doc = self.answer(self.start(stage=stage))
			photo = self.upload(doc)
			api.save_field_draft(doc.name, values={"image_upload": photo.file_url})
			api.complete_field_inspection(doc.name)
			for operation, args in (
				(api.save_field_draft, (doc.name,)),
				(self.upload, (doc,)),
				(frappe.delete_doc, (api.INSPECTION, doc.name)),
				(frappe.delete_doc, ("File", photo.name)),
			):
				with self.assertRaises(frappe.ValidationError):
					operation(*args)
			correction = api.create_field_correction(doc.name, "Correct mileage")
			corrected = frappe.get_doc(api.INSPECTION, correction["name"])
			self.assertEqual(corrected.corrects_inspection, doc.name)
			api.complete_field_inspection(corrected.name)
			self.assertEqual(doc.reload().inspection_status, "Completed")
			self.assertEqual(len(api.get_inspection_photos(corrected.name)), 1)

	def test_foreign_or_public_file_references_rejected(self):
		first, second = self.start(), self.start(card=self.cards[1])
		photo = self.upload(second)
		with self.assertRaises(frappe.ValidationError):
			api.save_field_draft(first.name, values={"image_upload": photo.file_url})
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "File",
					"file_name": "field-public.png",
					"content": b"invalid",
					"is_private": 0,
					"attached_to_doctype": api.INSPECTION,
					"attached_to_name": first.name,
				}
			).insert()

	def test_invalid_image_rejected_before_file_creation(self):
		doc = self.start()
		request = frappe._dict(
			files={"file": FileStorage(stream=BytesIO(b"not an image"), filename="fake.png")}
		)
		with (
			patch.object(frappe.local, "request", request, create=True),
			self.assertRaises(frappe.ValidationError),
		):
			api.upload_inspection_photo(doc.name)
		self.assertEqual(api.get_inspection_photos(doc.name), [])

	def test_technician_queries_and_direct_access_require_assignment(self):
		doc = self.start()
		self.field_user()
		self.assertEqual([row.name for row in api.get_field_jobs()], [self.cards[0].name])
		self.assertEqual(api.get_field_inspection(doc.name)["name"], doc.name)
		with self.assertRaises(frappe.PermissionError):
			api.get_field_job(self.cards[1].name)
		with self.assertRaises(frappe.PermissionError):
			api.start_inspection(self.cards[1].name, "Pre-Service", self.template.name)
		frappe.set_user("Administrator")
		self.todo.status = "Closed"
		self.todo.save()
		frappe.set_user(self.technician)
		with self.assertRaises(frappe.PermissionError):
			api.save_field_draft(doc.name)
		self.assertEqual(api.get_field_jobs(), [])

	def test_upload_owner_loses_photo_download_when_assignment_revoked(self):
		doc = self.start()
		self.field_user()
		photo = self.upload(doc)
		self.assertTrue(photo.is_downloadable())
		frappe.set_user("Administrator")
		self.todo.status = "Cancelled"
		self.todo.save()
		frappe.set_user(self.technician)
		self.assertFalse(photo.is_downloadable())
		with self.assertRaises(frappe.PermissionError):
			self.upload(doc)

	def test_active_employee_labour_assignment_is_permission_checked(self):
		self.field_user()
		frappe.set_user("Administrator")
		self.todo.status = "Cancelled"
		self.todo.save()
		employee = "Field Employee " + self.token
		frappe.db.bulk_insert(
			"Employee",
			fields=["name", "first_name", "employee_name", "company", "user_id", "status"],
			values=[(employee, "Field", "Field Test", self.cards[0].company, self.technician, "Active")],
		)
		frappe.db.bulk_insert(
			"Service Labour Entry",
			fields=["name", "parent", "parenttype", "parentfield", "technician", "docstatus"],
			values=[
				(
					"Field Labour " + self.token,
					self.cards[0].name,
					api.JOB_CARD,
					"labour_entries",
					employee,
					0,
				)
			],
		)
		frappe.set_user(self.technician)
		self.assertEqual(api.get_field_job(self.cards[0].name)["name"], self.cards[0].name)
		frappe.set_user("Administrator")
		frappe.db.set_value("Employee", employee, "status", "Left")
		frappe.set_user(self.technician)
		with self.assertRaises(frappe.PermissionError):
			api.get_field_job(self.cards[0].name)

	def test_permission_setup_is_idempotent_and_does_not_expand_related_access(self):
		from servicems.field_permissions import ensure_field_permissions

		audited = (api.JOB_CARD, api.INSPECTION, api.TEMPLATE)

		def other_permissions():
			return frappe.get_all(
				"Custom DocPerm",
				filters={"parent": ["not in", audited]},
				fields=["name", "parent", "role", "read", "write", "select"],
				order_by="name",
			)

		before = other_permissions()
		frappe.db.delete("Custom DocPerm", {"role": FIELD_ROLE, "parent": ["in", audited]})
		try:
			ensure_field_permissions()
			ensure_field_permissions()
			self.assertEqual(other_permissions(), before)
			self.assertEqual(
				frappe.db.count("Custom DocPerm", {"role": FIELD_ROLE, "parent": ["in", audited]}), 3
			)
		finally:
			frappe.clear_cache()

	def test_legacy_inspection_fields_hidden_and_existing_values_preserved(self):
		from servicems.inspection_migration import LEGACY_ACCEPTANCE_FIELDS

		for field in LEGACY_ACCEPTANCE_FIELDS:
			if field == "vin":
				continue
			meta = self.cards[0].meta.get_field(field)
			if meta:
				self.assertTrue(meta.hidden, field)
		self.cards[0].battery_make = "Historical battery evidence"
		self.cards[0].save()
		self.assertEqual(self.cards[0].reload().battery_make, "Historical battery evidence")
