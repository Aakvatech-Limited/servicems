# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	COMPANY,
	IGNORE_TEST_RECORD_DEPENDENCIES,
	PARTS_WAREHOUSE,
	WORKSHOP,
	WORKSHOP_WAREHOUSE,
)

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


def make_workshop(company):
	return frappe.get_doc(
		{
			"doctype": "Service Workshop",
			"workshop_name": "_Test SMS Workshop Other",
			"company": company,
			"parts_warehouse": PARTS_WAREHOUSE,
			"workshop_warehouse": WORKSHOP_WAREHOUSE,
		}
	).insert()


class TestServiceWorkshop(ServiceMSTestCase):
	def test_is_named_by_workshop_name(self):
		self.assertEqual(frappe.get_doc("Service Workshop", WORKSHOP).name, WORKSHOP)

	def test_company_follows_service_settings(self):
		other_company = frappe.db.get_value("Company", {"name": ["!=", COMPANY]})
		self.assertTrue(other_company)
		self.assertEqual(make_workshop(other_company).company, COMPANY)

	def test_company_falls_back_to_global_default(self):
		other_company = frappe.db.get_value("Company", {"name": ["!=", COMPANY]})
		frappe.db.set_single_value("Service Settings", "company", None)
		frappe.defaults.set_global_default("company", other_company)
		self.assertEqual(make_workshop(COMPANY).company, other_company)

	def test_company_kept_when_no_defaults(self):
		frappe.db.set_single_value("Service Settings", "company", None)
		frappe.defaults.set_global_default("company", None)
		self.assertEqual(make_workshop(COMPANY).company, COMPANY)

	def test_warehouses_are_mandatory(self):
		doc = frappe.get_doc(
			{"doctype": "Service Workshop", "workshop_name": "_Test SMS No Warehouse", "company": COMPANY}
		)
		self.assertRaises(frappe.MandatoryError, doc.insert)
