from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
	ServiceVehicleInspection,
)


class TestServiceVehicleInspection(UnitTestCase):
	def make_inspection(self, **kwargs):
		values = {"doctype": "Service Vehicle Inspection", "inspection_status": "Draft", "__islocal": 1}
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
		with patch.object(frappe, "get_doc"):
			with self.assertRaisesRegex(frappe.ValidationError, "Select an inspection template"):
				inspection.validate()

	def test_photos_are_required_even_when_template_opted_out(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Pre-Service",
			inspection_template="BASIC",
			template_snapshot="[]",
		)
		with patch.object(frappe, "get_doc"):
			with self.assertRaises(frappe.ValidationError):
				inspection.validate()

	def test_item_photo_rule_survives_stage_photo(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Post-Service",
			inspection_template="BASIC",
			image_upload="/files/stage.png",
		)
		row = inspection.append("checklist", {"inspection_item": "Damage", "require_photo": 1})
		template = SimpleNamespace(pre_inspection_items=[row], check_permission=lambda permission: None)
		with (
			patch.object(frappe, "get_doc", return_value=template),
			patch.object(frappe.db, "get_value", return_value=frappe._dict(name="photo", file_type="PNG")),
		):
			with self.assertRaisesRegex(frappe.ValidationError, "photograph is required for inspection item"):
				inspection.validate()
