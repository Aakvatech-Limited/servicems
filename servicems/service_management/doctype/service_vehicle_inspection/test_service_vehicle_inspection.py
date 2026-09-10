# Copyright (c) 2022, Aakvatech Limited and Contributors
# See license.txt

import frappe
from frappe.utils import nowdate

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import IGNORE_TEST_RECORD_DEPENDENCIES, VEHICLE_TYPE

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES

CHECKLISTS = {
	"service_lighting_checklist": {"lighting_check_item": "Head lamps", "lighting_mark": 1},
	"service_brake_checklist": {"brake_system": "Pads", "mark": 1, "brake_remarks": "OK"},
}


class TestServiceVehicleInspection(ServiceMSTestCase):
	def test_autoname_and_checklists(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Vehicle Inspection",
				"date": nowdate(),
				"driver_name": "Driver",
				"vehicle_plate_number": "T 123",
				"mileage": "1000",
				"service_vehicle_type": VEHICLE_TYPE,
				**{fieldname: [row] for fieldname, row in CHECKLISTS.items()},
			}
		).insert()
		self.assertTrue(doc.name.startswith("SVI"))
		self.assertEqual(doc.service_lighting_checklist[0].lighting_check_item, "Head lamps")
		self.assertEqual(doc.service_brake_checklist[0].mark, 1)

	def test_every_checklist_table_exists(self):
		meta = frappe.get_meta("Service Vehicle Inspection")
		tables = [field.options for field in meta.get_table_fields()]
		self.assertEqual(len(tables), 11)
		for table in tables:
			self.assertTrue(frappe.get_meta(table).istable, table)
