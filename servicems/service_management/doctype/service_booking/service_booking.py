# Copyright (c) 2024, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime


class ServiceBooking(Document):
	def validate(self):
		if self.bay and not frappe.db.get_single_value("Service Settings", "enable_bay_management"):
			previous_bay = None if self.is_new() else frappe.db.get_value("Service Booking", self.name, "bay")
			if self.bay != previous_bay:
				frappe.throw("Enable Bay Management in Service Settings before allocating a bay.")

	def before_insert(self):
		self.status = "Pending"
		self.posting_date = nowdate()
		self.posting_time = nowtime()

		if not self.workshop and self.bay:
			self.workshop = frappe.db.get_value("Bay", self.bay, "service_workshop")

	@frappe.whitelist()
	def close_booking(self):
		self.status = "Closed"
		self.save(ignore_permissions=True)


@frappe.whitelist()
def bulk_close_bookings(booking_list):
	booking_list = frappe.parse_json(booking_list)
	for booking in booking_list:
		if booking.status in ["Closed", "Completed"]:
			continue

		booking_doc = frappe.get_doc("Service Booking", booking)
		booking_doc.close_booking()

	return True
