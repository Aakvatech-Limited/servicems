# Copyright (c) 2022, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import IGNORE_TEST_RECORD_DEPENDENCIES, PARTS_ITEM_GROUP

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestSpare(ServiceMSTestCase):
	def test_named_by_item_code(self):
		spare = frappe.get_doc(
			{
				"doctype": "Spare",
				"item_code": "_Test SMS Spare",
				"item_group": PARTS_ITEM_GROUP,
				"stock_uom": "Nos",
			}
		).insert()
		self.assertEqual(spare.name, "_Test SMS Spare")

	def test_group_and_uom_are_mandatory(self):
		doc = frappe.get_doc({"doctype": "Spare", "item_code": "_Test SMS Spare 2"})
		self.assertRaises(frappe.MandatoryError, doc.insert)
