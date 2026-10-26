"""Date-based booking calendar and atomic booking creation."""

import re

import frappe
from frappe import _
from frappe.utils import date_diff, getdate


@frappe.whitelist()
def get_calendar_bookings(from_date, to_date, workshop=None, vehicle=None):
	"""Return individual bookings visible to the current user, including empty-bay bookings."""
	start, end = _date_range(from_date, to_date)
	filters = {"booking_date": ["between", [start, end]], "docstatus": ["<", 2]}
	for field, value in (("workshop", workshop), ("service_vehicle", vehicle)):
		if value:
			_validate_text(value, field)
			filters[field] = value

	bookings = frappe.get_list(
		"Service Booking",
		filters=filters,
		fields=[
			"name",
			"booking_date",
			"customer",
			"service_vehicle",
			"status",
			"workshop",
			"service_vehicle.vehicle_model as vehicle_model",
		],
		order_by="`tabService Booking`.booking_date asc, `tabService Booking`.creation asc, `tabService Booking`.name asc",
		page_length=10001,
	)
	if len(bookings) > 10000:
		frappe.throw(
			_("Too many bookings. Select a shorter date range or filter by Workshop or Service Vehicle.")
		)
	return bookings


@frappe.whitelist(methods=["POST"])
def create_booking(booking, new_customer=None, new_vehicle=None):
	"""Create related records in one request; Frappe rolls back the request on failure."""
	booking = _document_values(
		booking, ("customer", "service_vehicle", "booking_date", "workshop", "service_description")
	)
	_date_range(booking.get("booking_date"), booking.get("booking_date"))
	if not booking.get("workshop"):
		frappe.throw(_("Workshop is required."))
	frappe.has_permission("Service Booking", "create", throw=True)

	if new_customer is not None:
		customer = _document_values(
			new_customer,
			("customer_name", "customer_type", "customer_group", "territory", "tax_id", "mobile_no"),
		)
		booking["customer"] = frappe.get_doc({"doctype": "Customer", **customer}).insert().name
	if not booking.get("customer"):
		frappe.throw(_("Customer is required."))
	frappe.get_doc("Customer", booking["customer"]).check_permission("read")

	if new_vehicle is not None:
		vehicle = _document_values(
			new_vehicle, ("registration_number", "vehicle_model", "engine_number", "chassis_number")
		)
		if not vehicle.get("vehicle_model"):
			frappe.throw(_("Vehicle Model is required."))
		frappe.get_doc("Vehicle Model", vehicle["vehicle_model"]).check_permission("read")
		booking["service_vehicle"] = (
			frappe.get_doc({"doctype": "Service Vehicle", **vehicle, "customer": booking["customer"]})
			.insert()
			.name
		)
	if not booking.get("service_vehicle"):
		frappe.throw(_("Service Vehicle is required."))
	vehicle = frappe.get_doc("Service Vehicle", booking["service_vehicle"])
	vehicle.check_permission("read")
	if vehicle.customer != booking["customer"]:
		frappe.throw(_("The selected Service Vehicle does not belong to this Customer."))
	frappe.get_doc("Service Workshop", booking["workshop"]).check_permission("read")
	# Empty strings prevent Frappe from assigning the current time as a default.
	return (
		frappe.get_doc({"doctype": "Service Booking", **booking, "bay": "", "booking_time": ""})
		.insert()
		.as_dict()
	)


def _date_range(from_date, to_date):
	for value in (from_date, to_date):
		_validate_text(value, "Booking Date")
		if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
			frappe.throw(_("Select valid booking dates in YYYY-MM-DD format."))
	try:
		start, end = getdate(from_date), getdate(to_date)
	except (ValueError, TypeError):
		frappe.throw(_("Select valid booking dates."))
	if not 0 <= date_diff(end, start) <= 365:
		frappe.throw(_("Select a date range of at most 366 days, with To Date on or after From Date."))
	return start, end


def _document_values(value, fields):
	if isinstance(value, str):
		value = frappe.parse_json(value)
	if not isinstance(value, dict):
		frappe.throw(_("Expected document fields."))
	result = {}
	for field in fields:
		if value.get(field) is not None:
			_validate_text(value[field], field, allow_empty=True)
			result[field] = value[field]
	return result


def _validate_text(value, field, allow_empty=False):
	if not isinstance(value, str) or (not allow_empty and not value.strip()):
		frappe.throw(_("{0} must be text.").format(field))
