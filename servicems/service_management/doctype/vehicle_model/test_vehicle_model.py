# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import IGNORE_TEST_RECORD_DEPENDENCIES, VEHICLE_MAKE, VEHICLE_MODEL, VEHICLE_TYPE

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestVehicleModel(ServiceMSTestCase):
	def test_named_by_model_name_with_website_route(self):
		model = frappe.get_doc("Vehicle Model", VEHICLE_MODEL)
		self.assertEqual((model.make, model.type), (VEHICLE_MAKE, VEHICLE_TYPE))
		self.assertEqual(model.route, "vehicle_model/-test-sms-model")

	def test_route_follows_model_name(self):
		model = frappe.get_doc(
			{"doctype": "Vehicle Model", "model_name": "Test SMS Model Two", "make": VEHICLE_MAKE}
		).insert()
		self.assertEqual(model.route, "vehicle_model/test-sms-model-two")

	def test_masters(self):
		self.assertEqual(frappe.get_doc("Vehicle Make", VEHICLE_MAKE).make, VEHICLE_MAKE)
		self.assertEqual(frappe.get_doc("Service Vehicle Type", VEHICLE_TYPE).vehicle_type, VEHICLE_TYPE)
