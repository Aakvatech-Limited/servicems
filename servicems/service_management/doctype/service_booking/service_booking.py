# Copyright (c) 2024, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime


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
def bulk_close_bookings(booking_list: str | list):
	"""Close bookings given as names or as list view rows (dicts with a `name`)."""
	for booking in frappe.parse_json(booking_list):
		name = booking.get("name") if isinstance(booking, dict) else booking
		if frappe.db.get_value("Service Booking", name, "status") in ["Closed", "Completed"]:
			continue

		frappe.get_doc("Service Booking", name).close_booking()

	return True
