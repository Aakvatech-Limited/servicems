from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
	ServiceVehicleInspection,
)


class TestServiceVehicleInspection(UnitTestCase):
	def setUp(self):
		super().setUp()
		timer = patch(
			"servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection.now",
			return_value="2026-11-06 12:00:00",
		)
		timer.start()
		self.addCleanup(timer.stop)

	def make_inspection(self, **kwargs):
		values = {"doctype": "Service Vehicle Inspection", "inspection_status": "Draft", "__islocal": 1}
		values.update(kwargs)
		return ServiceVehicleInspection(values)

	def template(self, require_photographs=0, require_gps=0, items=None, stage=""):
		return SimpleNamespace(
			require_photographs=require_photographs,
			require_gps=require_gps,
			applicable_stage=stage,
			pre_inspection_items=items or [],
			check_permission=lambda permission: None,
		)

	def test_new_inspection_requires_template(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Select an inspection template"):
			self.make_inspection().validate()

	def test_draft_does_not_require_evidence_when_template_selected(self):
		inspection = self.make_inspection(inspection_template="BASIC", inspection_stage="Pre-Service")
		with patch.object(frappe, "get_doc", return_value=self.template()):
			inspection.validate()
		self.assertEqual(inspection.inspection_status, "Draft")
		self.assertEqual(inspection.require_photographs_snapshot, 0)

	def test_stage_mismatch_is_rejected(self):
		inspection = self.make_inspection(inspection_template="PRE", inspection_stage="Post-Service")
		with patch.object(frappe, "get_doc", return_value=self.template(stage="Pre-Service")):
			with self.assertRaisesRegex(frappe.ValidationError, "does not apply"):
				inspection.validate()

	def test_stage_photos_optional_when_template_opted_out(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Pre-Service",
			inspection_template="BASIC",
		)
		with patch.object(frappe, "get_doc", return_value=self.template(require_photographs=0)):
			inspection.validate()
		self.assertEqual(inspection.require_photographs_snapshot, 0)

	def test_stage_photo_required_when_template_enabled(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Pre-Service",
			inspection_template="BASIC",
		)
		with patch.object(frappe, "get_doc", return_value=self.template(require_photographs=1)):
			with self.assertRaisesRegex(frappe.ValidationError, "Attach at least one"):
				inspection.validate()

	def test_item_photo_rule_survives_optional_stage_photos(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Post-Service",
			inspection_template="BASIC",
		)
		spec = SimpleNamespace(
			inspection_item="Damage",
			inspection_type="Check",
			option="",
			require_photo=1,
			is_required=0,
			get=lambda field: getattr(spec, field),
		)
		with patch.object(frappe, "get_doc", return_value=self.template(items=[spec])):
			with self.assertRaisesRegex(frappe.ValidationError, "photograph is required"):
				inspection.validate()

	def test_required_answer_is_enforced(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Post-Service",
			inspection_template="BASIC",
		)
		spec = SimpleNamespace(
			inspection_item="Lights",
			inspection_type="Check",
			option="",
			require_photo=0,
			is_required=1,
			get=lambda field: getattr(spec, field),
		)
		with patch.object(frappe, "get_doc", return_value=self.template(items=[spec])):
			with self.assertRaisesRegex(frappe.ValidationError, "Answer required"):
				inspection.validate()

	def test_gps_required_by_template(self):
		inspection = self.make_inspection(
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Pre-Service",
			inspection_template="BASIC",
		)
		with patch.object(frappe, "get_doc", return_value=self.template(require_gps=1)):
			with self.assertRaisesRegex(frappe.ValidationError, "requires a GPS"):
				inspection.validate()

	def test_correction_requires_existing_record(self):
		inspection = self.make_inspection(
			inspection_template="BASIC", inspection_stage="Pre-Service", corrects_inspection="DONE"
		)
		source = SimpleNamespace(
			inspection_template="BASIC",
			inspection_status="Completed",
			service_job_card="SJC-001",
			inspection_stage="Pre-Service",
			template_snapshot="[]",
			require_photographs_snapshot=0,
			require_gps_snapshot=0,
			check_permission=lambda permission: None,
		)
		inspection.service_job_card = "SJC-001"
		inspection.correction_reason = "Incorrect mileage"

		def get_doc(doctype, name):
			if doctype == "Service Pre Inspection Template":
				return self.template()
			return source

		with patch.object(frappe, "get_doc", side_effect=get_doc):
			inspection.validate()
		self.assertEqual(inspection.require_photographs_snapshot, 0)
