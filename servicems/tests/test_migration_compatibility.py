import unittest

import frappe
from frappe.utils import add_to_date, now_datetime

from servicems.patches.v2_0.preserve_existing_bay_management import execute as preserve_bays
from servicems.tests import migration_fixtures as fixtures


class TestMigrationCompatibility(unittest.TestCase):
	"""Integration tests for disposable sites; every test rolls back its business records."""

	@classmethod
	def setUpClass(cls):
		if not frappe.conf.allow_tests:
			raise RuntimeError("Run migration fixtures only on a disposable site with allow_tests enabled")
		fixtures.create_test_data()
		if not frappe.db.exists("Gender", "Male"):
			frappe.get_doc({"doctype": "Gender", "gender": "Male"}).insert()
		if not frappe.db.exists("Employee", {"first_name": "_Test SMS Technician"}):
			frappe.get_doc(
				{
					"doctype": "Employee",
					"first_name": "_Test SMS Technician",
					"gender": "Male",
					"date_of_birth": "1990-01-01",
					"date_of_joining": "2020-01-01",
					"company": fixtures.COMPANY,
					"status": "Active",
				}
			).insert()
		frappe.db.commit()

	def setUp(self):
		frappe.db.savepoint("servicems_compatibility_test")
		self.addCleanup(self.restore_site)

	def restore_site(self):
		frappe.db.rollback(save_point="servicems_compatibility_test")
		frappe.clear_cache()

	def test_booking_without_bay_when_disabled(self):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 0)
		booking = fixtures.make_booking(bay=None)
		self.assertTrue(frappe.db.exists("Service Booking", booking.name))
		self.assertFalse(booking.bay)

	def test_new_bay_allocation_rejected_when_disabled(self):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 0)
		with self.assertRaises(frappe.ValidationError):
			fixtures.make_booking()

	def test_preservation_patch_keeps_explicit_disabled_setting(self):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
		fixtures.make_booking()
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 0)
		preserve_bays()
		self.assertEqual(frappe.db.get_single_value("Service Settings", "enable_bay_management"), 0)

	def test_preservation_patch_infers_legacy_allocations(self):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
		booking = fixtures.make_booking()
		frappe.db.delete("Singles", {"doctype": "Service Settings", "field": "enable_bay_management"})
		preserve_bays()
		self.assertEqual(
			frappe.db.get_single_value("Service Settings", "enable_bay_management", cache=False), 1
		)
		self.assertEqual(frappe.db.get_value("Service Booking", booking.name, "bay"), fixtures.BAY)

	def test_existing_bay_survives_save_when_feature_disabled(self):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
		booking = fixtures.make_booking()
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 0)
		booking.reload()
		booking.save()
		self.assertEqual(booking.bay, fixtures.BAY)

	def test_qc_default_and_historical_completion(self):
		frappe.db.set_single_value("Service Settings", "require_final_quality_check", 0)
		card = fixtures.complete_tasks(fixtures.make_job_card())
		card.save()
		frappe.db.set_single_value("Service Settings", "require_final_quality_check", 1)
		card.reload()
		card.save()
		self.assertFalse(card.quality_check_confirmed)

	def test_qc_required_for_new_completion(self):
		frappe.db.set_single_value("Service Settings", "require_final_quality_check", 1)
		card = fixtures.complete_tasks(fixtures.make_job_card())
		with self.assertRaises(frappe.ValidationError):
			card.save()
		card.reload()
		fixtures.complete_tasks(card)
		card.quality_check_confirmed = 1
		card.save()
		self.assertEqual(card.quality_checked_by, frappe.session.user)
		self.assertTrue(card.quality_checked_on)

	def test_technician_labour_start_stop_and_cross_card_guard(self):
		technician = frappe.db.get_value("Employee", {"first_name": "_Test SMS Technician"})
		first = fixtures.make_job_card()
		second = fixtures.make_job_card()
		first.start_labour(technician)
		with self.assertRaises(frappe.ValidationError):
			second.start_labour(technician)
		frappe.db.set_value(
			"Service Labour Entry",
			first.labour_entries[0].name,
			"started_at",
			add_to_date(now_datetime(), hours=-1),
		)
		first.reload()
		self.assertAlmostEqual(first.stop_labour(technician), 1.0, places=2)
		second.reload()
		second.start_labour(technician)
		self.assertEqual(second.labour_entries[0].technician, technician)

	def test_running_labour_blocks_completion(self):
		technician = frappe.db.get_value("Employee", {"first_name": "_Test SMS Technician"})
		card = fixtures.make_job_card()
		card.start_labour(technician)
		fixtures.complete_tasks(card)
		with self.assertRaises(frappe.ValidationError):
			card.save()
