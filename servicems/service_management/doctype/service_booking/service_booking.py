# Copyright (c) 2024, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, nowtime
from frappe.model.document import Document
from frappe.query_builder import DocType

class ServiceBooking(Document):
	def before_insert(self):
		self.status = "Pending"
		self.posting_date = nowdate()
		self.posting_time = nowtime()

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

@frappe.whitelist()
def get_service_bays(filters):
	b = DocType("Bay")
	sb = DocType("Service Booking")

	sb_query = (
		frappe.qb.from_(sb)
		.select(
			sb.status,
			sb.booking_time,
			sb.booking_date,
			sb.service_vehicle,
			sb.bay.as_("bay_name"),
			sb.name.as_("booking_id"),
		)
		.where(sb.status.isin(["Pending", "In Progress"])),
		orderby(sb.bay, sb.booking_date, sb.booking_time),
	)

	if filters.get("from_date"):
		sb_query = sb_query.where(sb.booking_date >= filters.get("from_date"))
	if filters.get("to_date"):
		sb_query = sb_query.where(sb.booking_date <= filters.get("to_date"))
	
	sb_data = sb_query.run(as_dict=True)

	bay_names = [bay.bay_name for bay in sb_data]

	bays = (
		frappe.qb.from_(b)
		.select(
			b.service_workshop,
			b.name.as_("bay_name"),
		)
		.where(b.name.isnotin(bay_names))
	).run(as_dict=True)

	sb_data.extend(bays)

	bays_data = sorted(sb_data, key=lambda x: x.get("bay_name"))

	return bays_data
