# Copyright (c) 2024, Aakvatech Limited and Contributors
# See license.txt

import frappe
from frappe.utils import nowdate

from servicems.service_management.doctype.service_booking.service_booking import bulk_close_bookings
from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	BAY,
	IGNORE_TEST_RECORD_DEPENDENCIES,
	WORKSHOP,
	complete_tasks,
	make_booking,
	make_job_card,
)

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES


class TestServiceBooking(ServiceMSTestCase):
	def test_insert_sets_status_and_posting_fields(self):
		booking = make_booking(status="Closed")
		self.assertEqual(booking.status, "Pending")
		self.assertEqual(str(booking.posting_date), nowdate())
		self.assertTrue(booking.posting_time)
		self.assertTrue(booking.name.startswith("SB-"))

	def test_workshop_is_derived_from_bay(self):
		booking = make_booking(workshop=None)
		self.assertEqual(booking.workshop, WORKSHOP)

	def test_bay_is_mandatory(self):
		self.assertRaises(frappe.MandatoryError, make_booking, bay=None)

	def test_close_booking(self):
		booking = make_booking()
		booking.close_booking()
		self.assertEqual(frappe.db.get_value("Service Booking", booking.name, "status"), "Closed")

	def test_bulk_close_with_names(self):
		first, second = make_booking(), make_booking(bay=BAY)
		self.assertTrue(bulk_close_bookings(frappe.as_json([first.name, second.name])))
		for booking in (first, second):
			self.assertEqual(frappe.db.get_value("Service Booking", booking.name, "status"), "Closed")

	def test_bulk_close_with_list_view_rows(self):
		"""The list view sends the checked rows as dicts, not names."""
		booking = make_booking()
		rows = [{"name": booking.name, "status": "Pending", "doctype": "Service Booking"}]
		self.assertTrue(bulk_close_bookings(frappe.as_json(rows)))
		self.assertEqual(frappe.db.get_value("Service Booking", booking.name, "status"), "Closed")

	def test_bulk_close_skips_completed(self):
		booking = make_booking()
		frappe.db.set_value("Service Booking", booking.name, "status", "Completed")
		bulk_close_bookings([booking.name])
		self.assertEqual(frappe.db.get_value("Service Booking", booking.name, "status"), "Completed")

	def test_job_card_moves_booking_to_in_progress_and_completed(self):
		booking = make_booking()
		job_card = make_job_card(service_booking=booking.name, bay=BAY)
		booking.reload()
		self.assertEqual(booking.status, "In Progress")
		self.assertEqual(booking.job_card, job_card.name)

		complete_tasks(job_card)
		job_card.save()
		frappe.db.set_value("Company Service Management Settings", job_card.company, "use_parts_entry", 1)
		job_card.submit()
		self.assertEqual(frappe.db.get_value("Service Booking", booking.name, "status"), "Completed")
