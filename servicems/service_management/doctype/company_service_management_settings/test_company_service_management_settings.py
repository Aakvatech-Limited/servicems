# Copyright (c) 2022, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import COMPANY, IGNORE_TEST_RECORD_DEPENDENCIES

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestCompanyServiceManagementSettings(ServiceMSTestCase):
	def test_named_by_company(self):
		settings = frappe.get_doc("Company Service Management Settings", COMPANY)
		self.assertEqual(settings.company, COMPANY)
		self.assertIn(settings.use_parts_entry, (0, 1))

	def test_one_record_per_company(self):
		doc = frappe.get_doc({"doctype": "Company Service Management Settings", "company": COMPANY})
		self.assertRaises(frappe.DuplicateEntryError, doc.insert)
