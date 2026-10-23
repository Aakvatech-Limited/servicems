import unittest
from unittest.mock import patch

import frappe
from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import ServiceVehicleInspection


class TestServiceVehicleInspection(unittest.TestCase):
	def make_inspection(self, **kwargs):
		values = {"doctype": "Service Vehicle Inspection", "inspection_status": "Draft"}
		values.update(kwargs)
		return ServiceVehicleInspection(values)

	def test_draft_does_not_require_evidence(self):
		self.make_inspection().validate()

	def test_completed_requires_job_card(self):
		inspection = self.make_inspection(inspection_status="Completed", inspection_stage="Pre-Service")
		with self.assertRaises(frappe.ValidationError):
			inspection.validate()

	def test_completed_requires_template(self):
		inspection = self.make_inspection(
			inspection_status="Completed", service_job_card="SJC-001", inspection_stage="Post-Service"
		)
		with self.assertRaises(frappe.ValidationError):
			inspection.validate()

	def test_template_with_photos_requires_evidence(self):
		inspection = self.make_inspection(
			inspection_status="Completed", service_job_card="SJC-001",
			inspection_stage="Pre-Service", inspection_template="BASIC"
		)
		with patch.object(frappe.db, "get_value", return_value=1):
			with self.assertRaises(frappe.ValidationError):
				inspection.validate()

	def test_template_without_photos_allows_completion(self):
		inspection = self.make_inspection(
			inspection_status="Completed", service_job_card="SJC-001",
			inspection_stage="Pre-Service", inspection_template="BASIC"
		)
		with patch.object(frappe.db, "get_value", return_value=0):
			inspection.validate()
