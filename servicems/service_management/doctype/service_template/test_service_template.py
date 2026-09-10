# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	IGNORE_TEST_RECORD_DEPENDENCIES,
	PART_ITEM,
	SERVICE_ITEM,
	SERVICE_TEMPLATE,
	TASK_A,
	TEMPLATE_PART_QTY,
)

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestServiceTemplate(ServiceMSTestCase):
	def test_template_structure(self):
		template = frappe.get_doc("Service Template", SERVICE_TEMPLATE)
		self.assertEqual((template.item, template.is_billable), (SERVICE_ITEM, 1))
		self.assertEqual(len(template.tasks), 2)
		self.assertEqual((template.parts[0].item, template.parts[0].qty), (PART_ITEM, TEMPLATE_PART_QTY))

	def test_tasks_are_mandatory(self):
		doc = frappe.get_doc(
			{"doctype": "Service Template", "template_name": "_Test SMS No Tasks", "item": SERVICE_ITEM}
		)
		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_part_qty_is_mandatory(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Template",
				"template_name": "_Test SMS No Qty",
				"item": SERVICE_ITEM,
				"tasks": [{"task_name": TASK_A}],
				"parts": [{"item": PART_ITEM}],
			}
		)
		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_service_task_master(self):
		self.assertEqual(frappe.get_doc("Service Task", TASK_A).task_name, TASK_A)
