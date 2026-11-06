# Copyright (c) 2024, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_time, nowdate, nowtime


class ServiceBooking(Document):
	def validate(self):
		if not self.bay:
			return
		if not frappe.db.get_single_value("Service Settings", "enable_bay_management"):
			previous_bay = None if self.is_new() else frappe.db.get_value("Service Booking", self.name, "bay")
			if self.bay != previous_bay:
				frappe.throw("Enable Bay Management in Service Settings before allocating a bay.")
			return
		if self.status not in ("Pending", "In Progress") or self.docstatus == 2:
			return
		previous = self.get_doc_before_save()
		changed = self.is_new() or any(
			self.has_value_changed(field) for field in ("bay", "workshop", "booking_date", "booking_time")
		)
		if changed or (previous and previous.status not in ("Pending", "In Progress")):
			from servicems.api.calendar import _validate_bay

			booking_time = (
				get_time(self.booking_time).strftime("%H:%M:%S")
				if self.booking_time not in (None, "")
				else ""
			)
			_validate_bay(self.bay, self.workshop, self.booking_date, booking_time, exclude=self.name)

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
