# Copyright (c) 2024, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import BAY, IGNORE_TEST_RECORD_DEPENDENCIES, WORKSHOP

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestBay(ServiceMSTestCase):
	def test_is_named_by_bay_field(self):
		bay = frappe.get_doc("Bay", BAY)
		self.assertEqual(bay.bay, BAY)
		self.assertEqual(bay.service_workshop, WORKSHOP)

	def test_unknown_workshop_is_rejected(self):
		doc = frappe.get_doc(
			{"doctype": "Bay", "bay": "_Test SMS Bay Bad", "service_workshop": "_Test SMS Missing"}
		)
		self.assertRaises(frappe.LinkValidationError, doc.insert)

	def test_duplicate_bay_is_rejected(self):
		doc = frappe.get_doc({"doctype": "Bay", "bay": BAY, "service_workshop": WORKSHOP})
		self.assertRaises(frappe.DuplicateEntryError, doc.insert)
