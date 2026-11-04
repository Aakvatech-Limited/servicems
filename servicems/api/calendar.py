"""Permission-aware data and actions for the ServiceMS Booking Calendar.

Bookings have a start time but no service duration. Bay conflict prevention therefore
covers only identical explicit start times, not overlapping appointment intervals.
"""

import re

import frappe
from frappe import _
from frappe.utils import date_diff, getdate

ACTIVE_STATUSES = ("Pending", "In Progress")
BOOKING_STATUSES = ("Pending", "In Progress", "Completed", "Closed")


def _date_range(from_date, to_date):
    for value in (from_date, to_date):
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            frappe.throw(_("Booking dates must be in YYYY-MM-DD format."))
    try:
        start, end = getdate(from_date), getdate(to_date)
    except (TypeError, ValueError):
        frappe.throw(_("Select valid booking dates."))
    if not 0 <= date_diff(end, start) <= 365:
        frappe.throw(_("Select a date range of at most 366 days."))
    return start, end


def _text(value, field, *, allow_empty=False, limit=140):
    if not isinstance(value, str) or len(value) > limit or (not allow_empty and not value.strip()):
        frappe.throw(_("{0} must be valid text.").format(field))
    return value.strip()


def _time(value):
    if value in (None, ""):
        return ""
    value = _text(value, "Booking Time", limit=8)
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value):
        frappe.throw(_("Booking Time must use HH:MM or HH:MM:SS."))
    return value


def _as_values(value, fields):
    if isinstance(value, str):
        value = frappe.parse_json(value)
    if not isinstance(value, dict):
        frappe.throw(_("Expected document fields."))
    result = {}
    for field in fields:
        if field in value:
            result[field] = _text(value[field], field, allow_empty=True, limit=1000 if field == "service_description" else 140)
    return result


def _bay_enabled():
    return bool(frappe.db.get_single_value("Service Settings", "enable_bay_management"))


def _validate_bay(bay, workshop, booking_date, booking_time, exclude=None):
    if not bay:
        return
    if not _bay_enabled():
        frappe.throw(_("Bay Management is disabled."))
    bay_doc = frappe.get_doc("Bay", bay)
    bay_doc.check_permission("read")
    if bay_doc.service_workshop != workshop:
        frappe.throw(_("The selected Bay does not belong to this Workshop."))
    # No duration field exists; do not claim to detect overlapping intervals.
    if booking_time:
        filters = {
            "bay": bay,
            "booking_date": booking_date,
            "booking_time": booking_time,
            "status": ["in", ACTIVE_STATUSES],
        }
        if exclude:
            filters["name"] = ["!=", exclude]
        if frappe.get_all("Service Booking", filters=filters, limit=1, pluck="name"):
            frappe.throw(_("This Bay already has a booking at the selected start time."))


def _enrich(bookings):
    customer_names = sorted({row.customer for row in bookings if row.customer})
    vehicle_names = sorted({row.service_vehicle for row in bookings if row.service_vehicle})
    customers = {
        row.name: row.customer_name
        for row in frappe.get_list(
            "Customer", filters={"name": ["in", customer_names]},
            fields=["name", "customer_name"], page_length=len(customer_names),
        )
    } if customer_names else {}
    vehicles = {
        row.name: row
        for row in frappe.get_list(
            "Service Vehicle", filters={"name": ["in", vehicle_names]},
            fields=["name", "registration_number", "vehicle_model"],
            page_length=len(vehicle_names),
        )
    } if vehicle_names else {}
    result = []
    for row in bookings:
        vehicle = vehicles.get(row.service_vehicle)
        result.append({
            "name": row.name,
            "booking_date": str(row.booking_date),
            "booking_time": str(row.booking_time or ""),
            "customer": row.customer,
            "customer_name": customers.get(row.customer, row.customer),
            "service_vehicle": row.service_vehicle,
            "registration_number": vehicle.registration_number if vehicle else row.service_vehicle,
            "vehicle_model": vehicle.vehicle_model if vehicle else "",
            "workshop": row.workshop,
            "bay": row.bay,
            "status": row.status,
            "job_card": row.job_card,
        })
    return result


@frappe.whitelist()
def get_calendar_bookings(from_date, to_date, workshop=None, vehicle=None, status=None, search=None):
    """Return individually permission-filtered bookings and optional visible Bays."""
    start, end = _date_range(from_date, to_date)
    filters = {"booking_date": ["between", [start, end]], "docstatus": ["<", 2]}
    if workshop:
        filters["workshop"] = _text(workshop, "Workshop")
    if vehicle:
        filters["service_vehicle"] = _text(vehicle, "Vehicle")
    if status:
        if status not in BOOKING_STATUSES:
            frappe.throw(_("Unsupported booking status."))
        filters["status"] = status
    if search:
        search = _text(search, "Search", limit=100).casefold()

    bookings = frappe.get_list(
        "Service Booking",
        filters=filters,
        fields=["name", "booking_date", "booking_time", "customer",
                "service_vehicle", "workshop", "bay", "status", "job_card"],
        order_by="booking_date asc, booking_time asc, creation asc",
        page_length=10001,
    )
    if len(bookings) > 10000:
        frappe.throw(_("Too many bookings. Select a shorter date range or filter the results."))

    result = _enrich(bookings)
    if search:
        result = [
            row for row in result
            if any(search in str(row.get(field) or "").casefold()
                   for field in ("name", "customer_name", "registration_number", "service_vehicle"))
        ]
    bay_management_enabled = _bay_enabled()
    bays = []
    if bay_management_enabled:
        bay_filters = {"service_workshop": workshop} if workshop else {}
        bays = frappe.get_list(
            "Bay", fields=["name", "service_workshop"], filters=bay_filters,
            order_by="name asc", page_length=1000,
        )
    return {"bookings": result, "bay_management_enabled": bay_management_enabled, "bays": bays}


@frappe.whitelist(methods=["POST"])
def create_booking(booking, new_customer=None, new_vehicle=None):
    """Create a booking and optional new customer/vehicle in one DB transaction."""
    values = _as_values(
        booking,
        ("customer", "service_vehicle", "booking_date", "booking_time",
         "workshop", "bay", "service_description"),
    )
    _date_range(values.get("booking_date"), values.get("booking_date"))
    values["booking_time"] = _time(values.get("booking_time"))
    if not values.get("workshop"):
        frappe.throw(_("Workshop is required."))
    frappe.has_permission("Service Booking", "create", throw=True)
    frappe.get_doc("Service Workshop", values["workshop"]).check_permission("read")

    if new_customer is not None:
        customer = _as_values(
            new_customer,
            ("customer_name", "customer_type", "customer_group", "territory", "tax_id", "mobile_no"),
        )
        values["customer"] = frappe.get_doc({"doctype": "Customer", **customer}).insert().name
    if not values.get("customer"):
        frappe.throw(_("Customer is required."))
    frappe.get_doc("Customer", values["customer"]).check_permission("read")

    if new_vehicle is not None:
        vehicle = _as_values(
            new_vehicle, ("registration_number", "vehicle_model", "engine_number", "chassis_number"),
        )
        if not vehicle.get("vehicle_model"):
            frappe.throw(_("Vehicle Model is required."))
        frappe.get_doc("Vehicle Model", vehicle["vehicle_model"]).check_permission("read")
        values["service_vehicle"] = frappe.get_doc({
            "doctype": "Service Vehicle", **vehicle, "customer": values["customer"],
        }).insert().name
    if not values.get("service_vehicle"):
        frappe.throw(_("Service Vehicle is required."))
    vehicle_doc = frappe.get_doc("Service Vehicle", values["service_vehicle"])
    vehicle_doc.check_permission("read")
    if vehicle_doc.customer != values["customer"]:
        frappe.throw(_("The selected Vehicle does not belong to the Customer."))

    _validate_bay(values.get("bay"), values["workshop"], values["booking_date"], values["booking_time"])
    return frappe.get_doc({"doctype": "Service Booking", **values}).insert().as_dict()


@frappe.whitelist(methods=["POST"])
def reschedule_booking(name, booking_date, booking_time="", bay=None):
    """Change pending bookings only, using the existing document validations."""
    _text(name, "Booking", limit=140)
    _date_range(booking_date, booking_date)
    booking_time = _time(booking_time)
    doc = frappe.get_doc("Service Booking", name)
    doc.check_permission("write")
    if doc.status != "Pending":
        frappe.throw(_("Only pending bookings can be rescheduled."))
    effective_bay = doc.bay if bay is None else _text(bay, "Bay", allow_empty=True)
    _validate_bay(effective_bay, doc.workshop, booking_date, booking_time, exclude=doc.name)
    doc.booking_date = booking_date
    doc.booking_time = booking_time
    if bay is not None:
        doc.bay = effective_bay
    doc.save()
    return {"name": doc.name, "booking_date": str(doc.booking_date),
            "booking_time": str(doc.booking_time or ""), "bay": doc.bay}
