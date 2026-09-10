# Copyright (c) 2022, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import COMPANY, IGNORE_TEST_RECORD_DEPENDENCIES, PART_ITEM

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


def make_parts_entry(items):
	return frappe.get_doc({"doctype": "Service Parts Entry", "company": COMPANY, "items": items})


class TestServicePartsEntry(ServiceMSTestCase):
	def test_submit_and_cancel(self):
		entry = make_parts_entry([{"item_code": PART_ITEM, "qty": 2, "basic_rate": 10}]).insert()
		self.assertTrue(entry.name.startswith("ServMS-PTE-"))
		entry.submit()
		self.assertEqual(entry.docstatus, 1)
		entry.cancel()
		self.assertEqual(entry.docstatus, 2)

	def test_items_are_mandatory(self):
		self.assertRaises(frappe.MandatoryError, make_parts_entry([]).insert)

	def test_item_qty_is_mandatory(self):
		self.assertRaises(frappe.MandatoryError, make_parts_entry([{"item_code": PART_ITEM}]).insert)
