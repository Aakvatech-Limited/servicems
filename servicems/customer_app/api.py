"""Customer-only endpoints. Never expose the internal Booking Calendar API directly."""

import frappe
from frappe import _
from frappe.utils import cint

from servicems.customer_app.security import (
	enabled_settings,
	enabled_workshop,
	require_customers,
)


def _start(value):
	try:
		return max(0, min(cint(value), 10000))
	except (ValueError, TypeError):
		return 0


@frappe.whitelist()
def get_available_workshops(company):
	"""Workshop availability is for NEW bookings, never historical visibility."""
	require_customers(company)
	settings_name = enabled_settings(company)
	rows = frappe.get_all(
		"Customer App Workshop Availability",
		filters={"parent": settings_name, "parenttype": "Customer App Settings", "booking_enabled": 1},
		fields=["workshop"],
	)
	workshops = sorted({row.workshop for row in rows})
	if not workshops:
		return []
	return frappe.get_all(
		"Service Workshop",
		filters={"name": ["in", workshops], "company": company},
		fields=["name", "workshop_name", "location"],
		order_by="workshop_name asc",
		page_length=len(workshops),
	)


@frappe.whitelist()
def get_my_job_cards(company, start=0):
	customers = require_customers(company)
	return frappe.get_all(
		"Service Job Card",
		filters={"company": company, "customer": ["in", customers], "docstatus": ["<", 2]},
		fields=["name", "status", "workshop", "service_item_name", "receiving_datetime"],
		order_by="receiving_datetime desc",
		start=_start(start),
		page_length=50,
	)


@frappe.whitelist()
def get_my_quotations(company, start=0):
	customers = require_customers(company)
	return frappe.get_all(
		"Quotation",
		filters={"company": company, "quotation_to": "Customer", "party_name": ["in", customers], "docstatus": 1},
		fields=["name", "transaction_date", "status", "grand_total", "currency", "valid_till"],
		order_by="transaction_date desc",
		start=_start(start),
		page_length=50,
	)


@frappe.whitelist()
def get_my_invoices(company, start=0):
	customers = require_customers(company)
	return frappe.get_all(
		"Sales Invoice",
		filters={"company": company, "customer": ["in", customers], "docstatus": 1},
		fields=["name", "posting_date", "status", "grand_total", "outstanding_amount", "currency"],
		order_by="posting_date desc",
		start=_start(start),
		page_length=50,
	)


@frappe.whitelist()
def get_my_bookings(company, start=0):
	customers = require_customers(company)
	workshops = frappe.get_all("Service Workshop", filters={"company": company}, pluck="name")
	if not workshops:
		return []
	return frappe.get_all(
		"Service Booking",
		filters={"workshop": ["in", workshops], "customer": ["in", customers], "docstatus": ["<", 2]},
		fields=["name", "booking_date", "booking_time", "status", "workshop", "service_vehicle", "job_card"],
		order_by="booking_date desc",
		start=_start(start),
		page_length=50,
	)


@frappe.whitelist(methods=["POST"])
def create_customer_booking(company, customer, workshop, service_vehicle, booking_date, booking_time="", description=""):
	"""Create only on the user's verified Customer and a currently enabled workshop."""
	customers = require_customers(company)
	if customer not in customers:
		frappe.throw(_("Customer is not authorized."), frappe.PermissionError)
	enabled_workshop(company, workshop)
	if frappe.db.get_value("Service Vehicle", service_vehicle, "customer") != customer:
		frappe.throw(_("Vehicle is not authorized."), frappe.PermissionError)
	from servicems.api.calendar import _date_range, _time

	_date_range(booking_date, booking_date)
	booking_time = _time(booking_time)
	if not isinstance(description, str) or len(description) > 1000:
		frappe.throw(_("Service description is too long."))
	return frappe.get_doc(
		{
			"doctype": "Service Booking",
			"customer": customer,
			"workshop": workshop,
			"service_vehicle": service_vehicle,
			"booking_date": booking_date,
			"booking_time": booking_time,
			"service_description": description,
		}
	).insert(ignore_permissions=True).name
