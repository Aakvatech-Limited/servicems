from unittest.mock import patch

import frappe

from servicems import fleet_integration
from servicems.tests.base import ServiceMSTestCase

FLEET_DOCTYPES = ["Tyre Master", "Tyre Position", "Trailers"]
TYRE_FIELDS = [
	"custom_trailer",
	"tyre_management_section",
	"tyre_serial",
	"tyre_movement_type",
	"tyre_install_on",
	"tyre_from_position",
	"tyre_to_position",
	"tyre_position",
]


get_installed_apps = frappe.get_installed_apps


def installed_with_fleet():
	return [*get_installed_apps(), "vsd_fleet_ms"]


def tyre_custom_fields():
	return frappe.get_all(
		"Custom Field",
		filters={"dt": "Service Job Card", "fieldname": ["in", TYRE_FIELDS]},
		pluck="fieldname",
	)


class TestFleetIntegration(ServiceMSTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.remove_tyre_fields()

	def test_noop_without_fleet_app(self):
		fleet_integration.ensure_service_job_card_tyre_fields()
		self.assertEqual(tyre_custom_fields(), [])

	def test_noop_when_fleet_doctypes_missing(self):
		with patch("frappe.get_installed_apps", installed_with_fleet):
			fleet_integration.ensure_service_job_card_tyre_fields()
		self.assertEqual(tyre_custom_fields(), [])

	def test_creates_tyre_fields_when_fleet_present(self):
		for doctype in FLEET_DOCTYPES:
			if not frappe.db.exists("DocType", doctype):
				frappe.get_doc(
					{
						"doctype": "DocType",
						"name": doctype,
						"module": "Service Management",
						"custom": 1,
						"fields": [{"fieldname": "title", "fieldtype": "Data", "label": "Title"}],
						"permissions": [{"role": "System Manager"}],
					}
				).insert()
				self.addCleanup(self.remove_doctype, doctype)
		self.addCleanup(self.remove_tyre_fields)

		with patch("frappe.get_installed_apps", installed_with_fleet):
			fleet_integration.ensure_service_job_card_tyre_fields()
			fleet_integration.ensure_service_job_card_tyre_fields()

		self.assertEqual(sorted(tyre_custom_fields()), sorted(TYRE_FIELDS))
		meta = frappe.get_meta("Service Job Card")
		self.assertEqual(meta.get_field("tyre_serial").options, "Tyre Master")
		self.assertEqual(meta.get_field("custom_trailer").options, "Trailers")
		self.assertIn("Positional Change", meta.get_field("tyre_movement_type").options)

	def test_no_placeholder_user_data_fields(self):
		for row in frappe.get_hooks("user_data_fields", app_name="servicems"):
			self.assertTrue(frappe.db.exists("DocType", row["doctype"]), row)

	def test_hooks_are_registered(self):
		target = "servicems.fleet_integration.ensure_service_job_card_tyre_fields"
		self.assertIn(target, frappe.get_hooks("after_migrate", app_name="servicems"))
		self.assertIn(target, frappe.get_hooks("after_install", app_name="servicems"))

	@classmethod
	def remove_tyre_fields(cls):
		"""Custom field creation alters the table (implicit commit), so the cleanup commits too."""
		for name in frappe.get_all(
			"Custom Field", filters={"dt": "Service Job Card", "fieldname": ["in", TYRE_FIELDS]}, pluck="name"
		):
			frappe.delete_doc("Custom Field", name, force=True)
		frappe.clear_cache(doctype="Service Job Card")
		frappe.db.commit()  # nosemgrep

	def remove_doctype(self, doctype):
		frappe.delete_doc("DocType", doctype, force=True)
		frappe.db.commit()  # nosemgrep
