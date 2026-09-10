# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import IGNORE_TEST_RECORD_DEPENDENCIES

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestServicePreInspectionTemplate(ServiceMSTestCase):
	def test_named_by_template_with_items(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Pre Inspection Template",
				"template_name": "_Test SMS Pre Inspection",
				"pre_inspection_items": [
					{"inspection_item": "Lights", "inspection_type": "Check"},
					{"inspection_item": "Fuel level", "inspection_type": "Data", "option": "Litres"},
				],
			}
		).insert()
		self.assertEqual(doc.name, "_Test SMS Pre Inspection")
		self.assertEqual([row.inspection_type for row in doc.pre_inspection_items], ["Check", "Data"])

	def test_invalid_inspection_type_is_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Pre Inspection Template",
				"template_name": "_Test SMS Bad Type",
				"pre_inspection_items": [{"inspection_item": "Lights", "inspection_type": "Toggle"}],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
