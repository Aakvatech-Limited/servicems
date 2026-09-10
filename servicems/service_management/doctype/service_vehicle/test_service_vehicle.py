# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	CUSTOMER,
	IGNORE_TEST_RECORD_DEPENDENCIES,
	VEHICLE,
	VEHICLE_MAKE,
	VEHICLE_MODEL,
	VEHICLE_TYPE,
)

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestServiceVehicle(ServiceMSTestCase):
	def test_named_by_registration_number(self):
		vehicle = frappe.get_doc("Service Vehicle", VEHICLE)
		self.assertEqual(vehicle.registration_number, VEHICLE)

	def test_fetches_model_and_customer_details(self):
		vehicle = frappe.get_doc("Service Vehicle", VEHICLE)
		self.assertEqual((vehicle.make, vehicle.type), (VEHICLE_MAKE, VEHICLE_TYPE))
		self.assertEqual(vehicle.mobile_no, "0700000001")

	def test_duplicate_registration_is_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Vehicle",
				"registration_number": VEHICLE,
				"customer": CUSTOMER,
				"vehicle_model": VEHICLE_MODEL,
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, doc.insert)

	def test_customer_and_model_are_mandatory(self):
		doc = frappe.get_doc({"doctype": "Service Vehicle", "registration_number": "_TSMS 999"})
		self.assertRaises(frappe.MandatoryError, doc.insert)
