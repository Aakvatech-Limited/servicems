# Copyright (c) 2024, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, nowtime
from frappe.model.document import Document

class ServiceBooking(Document):
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
