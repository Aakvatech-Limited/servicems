"""Real-record sequencing, visibility and privacy regressions for UAT."""

from types import SimpleNamespace
from unittest import TestCase

import frappe

from servicems import field_api as api
from servicems.inspection_workflow import finished, repair_complete, stage_state
from servicems.tests import test_field_operations as fixtures


class TestFieldFinalization(TestCase):
	setUp = fixtures.TestFieldOperations.setUp
	start = fixtures.TestFieldOperations.start
	answer = fixtures.TestFieldOperations.answer
	upload = fixtures.TestFieldOperations.upload
	field_user = fixtures.TestFieldOperations.field_user

	def tearDown(self):
		fixtures.TestFieldOperations.tearDown(self)
		frappe.clear_document_cache("Service Settings", "Service Settings")

	def policy(self, pre="Optional", post="Optional", gps=0):
		for key, value in {
			"pre_inspection_policy": pre,
			"post_inspection_policy": post,
			"field_gps_enabled": gps,
		}.items():
			frappe.db.set_single_value("Service Settings", key, value)
		frappe.clear_document_cache("Service Settings", "Service Settings")

	def repair(self, card=None):
		card = (card or self.cards[0]).reload()
		for task in card.tasks:
			task.completed = 1
		card.save()
		return card

	def post(self, card=None):
		self.template.applicable_stage = "Post-Service"
		self.template.save()
		return self.start(stage="Post-Service", card=card)

	def finish(self):
		self.policy()
		self.repair()
		doc = self.answer(self.post())
		api.complete_field_inspection(doc.name)
		return doc.reload()

	def test_required_pre_blocks_desk_repair_and_post_until_completed(self):
		self.policy(pre="Required")
		with self.assertRaisesRegex(frappe.ValidationError, "required Pre-Inspection"):
			self.repair()
		card = self.cards[0].reload()
		card.status = "Repairing"
		with self.assertRaises(frappe.ValidationError):
			card.save()
		with self.assertRaises(frappe.ValidationError):
			self.post()
		self.template.applicable_stage = "Pre-Service"
		self.template.save()
		api.complete_field_inspection(self.answer(self.start()).name)
		self.repair()
		self.assertTrue(self.post().name)

	def test_post_rejected_until_all_tasks_complete_in_desk_and_api(self):
		self.policy()
		with self.assertRaisesRegex(frappe.ValidationError, "repair tasks"):
			self.post()
		self.repair()
		doc = self.answer(self.post())
		card = self.cards[0].reload()
		card.tasks[0].completed = 0
		card.save()
		doc.inspection_status = "Completed"
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		with self.assertRaises(frappe.ValidationError):
			api.complete_field_inspection(doc.name)

	def test_optional_pre_draft_does_not_block_repairs(self):
		self.policy()
		doc = self.start()
		self.repair()
		self.assertTrue(api.get_field_inspection(doc.name).field_read_only_reason)
		self.assertTrue(self.post().name)

	def test_disabled_stages_preserve_templates_and_allow_repairs(self):
		self.policy(pre="Disabled", post="Disabled")
		with self.assertRaisesRegex(frappe.ValidationError, "disabled"):
			self.start()
		self.repair()
		with self.assertRaisesRegex(frappe.ValidationError, "disabled"):
			self.post()
		self.assertTrue(frappe.db.exists(api.TEMPLATE, self.template.name))

	def test_no_tasks_does_not_require_artificial_job_completion(self):
		self.policy()
		card = self.cards[0]
		card.tasks = []
		card.save()
		self.assertTrue(self.post().name)
		self.assertEqual(card.reload().status, "Active")

	def test_running_labour_blocks_post_even_when_tasks_complete(self):
		card = SimpleNamespace(
			tasks=[SimpleNamespace(completed=1)],
			labour_entries=[SimpleNamespace(started_at="2026-11-07", stopped_at=None)],
		)
		self.assertFalse(repair_complete(card))
		card.labour_entries[0].stopped_at = "2026-11-07 15:00:00"
		self.assertTrue(repair_complete(card))

	def test_required_post_gates_job_completion_without_changing_status_itself(self):
		self.policy(post="Required")
		card = self.repair()
		card.status = "Completed"
		with self.assertRaisesRegex(frappe.ValidationError, "required Post-Inspection"):
			card.save()
		doc = self.answer(self.post())
		api.complete_field_inspection(doc.name)
		self.assertEqual(card.reload().status, "Active")
		card.status = "Completed"
		card.save()
		self.assertTrue(finished(card.name))

	def test_post_completion_hides_only_finished_job_and_all_field_direct_access(self):
		doc = self.finish()
		self.field_user()
		self.assertEqual(api.get_field_jobs(), [])
		for operation, args in (
			(api.get_field_job, (self.cards[0].name,)),
			(api.get_job_inspections, (self.cards[0].name,)),
			(api.get_field_inspection, (doc.name,)),
			(api.get_inspection_photos, (doc.name,)),
			(api.save_field_draft, (doc.name,)),
			(api.upload_inspection_photo, (doc.name,)),
			(api.create_field_correction, (doc.name, "Not ordinary Field work")),
		):
			with self.subTest(operation=operation.__name__), self.assertRaises(frappe.ValidationError):
				operation(*args)
		frappe.set_user("Administrator")
		self.assertTrue(frappe.get_doc(api.INSPECTION, doc.name).check_permission("read") is None)
		self.assertEqual(self.cards[0].reload().status, "Active")

	def test_finished_history_and_desk_corrections_remain_protected(self):
		doc = self.finish()
		correction = doc.create_correction("Authorized Desk correction")
		self.assertTrue(finished(doc.service_job_card))
		self.assertEqual(frappe.get_doc(api.INSPECTION, correction).corrects_inspection, doc.name)
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(api.INSPECTION, doc.name)
		self.field_user()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(api.INSPECTION, doc.name).create_correction("Direct Field REST bypass")

	def test_ordinary_desk_inspection_cannot_restart_finished_work(self):
		self.finish()
		with self.assertRaises(frappe.ValidationError):
			self.post()

	def test_finished_visibility_ignores_job_status_and_later_stage_settings(self):
		doc = self.finish()
		self.policy(pre="Disabled", post="Disabled")
		for status in ("Active", "Completed", "Closed"):
			frappe.db.set_value(api.JOB_CARD, doc.service_job_card, "status", status)
			self.assertTrue(finished(doc.service_job_card))
			self.assertNotIn(doc.service_job_card, [row.name for row in api.get_field_jobs()])

	def test_historical_post_does_not_require_a_backdated_pre_for_billing_completion(self):
		doc = self.finish()
		self.policy(pre="Required", post="Required")
		card = self.cards[0].reload()
		card.status = "Completed"
		card.save()
		self.assertTrue(finished(doc.service_job_card))
		card.status = "Repairing"
		with self.assertRaisesRegex(frappe.ValidationError, "new Job Card"):
			card.save()

	def test_pre_inspection_cannot_be_backdated_after_repair(self):
		self.policy()
		self.repair()
		with self.assertRaisesRegex(frappe.ValidationError, "before repair"):
			self.start()

	def test_stage_settings_and_gps_preferences_are_permission_aware(self):
		self.policy(pre="Required", post="Disabled", gps=1)
		self.field_user()
		self.assertTrue(api.get_field_options()["gps_enabled"])
		self.assertEqual(api.set_field_gps_preference("disabled")["gps_preference"], "disabled")
		self.assertEqual(api.get_field_options()["gps_preference"], "disabled")
		with self.assertRaises(frappe.ValidationError):
			api.set_field_gps_preference("another-user")
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("Service Settings").check_permission("write")
		states = stage_state(self.cards[0])
		self.assertEqual(states["Pre-Service"]["policy"], "Required")
		self.assertTrue(states["Post-Service"]["reason"])

	def test_finished_filter_does_not_truncate_the_next_permitted_job(self):
		self.finish()
		jobs = api.get_field_jobs(limit=1)
		self.assertEqual(len(jobs), 1)
		self.assertNotEqual(jobs[0].name, self.cards[0].name)
