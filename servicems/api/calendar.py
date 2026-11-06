"""Permission-aware data and actions for the ServiceMS Booking Calendar.

Bookings have a start time but no service duration. Bay conflict prevention therefore
covers only identical explicit start times, not overlapping appointment intervals.
"""

import re

import frappe
from frappe import _
from frappe.utils import cint, date_diff, get_system_timezone, getdate, strip_html_tags

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
			result[field] = _text(
				value[field], field, allow_empty=True, limit=1000 if field == "service_description" else 140
			)
	return result


def _bay_enabled():
	return bool(frappe.db.get_single_value("Service Settings", "enable_bay_management"))


def _validate_bay(bay, workshop, booking_date, booking_time, exclude=None):
	if not bay:
		return
	if not _bay_enabled():
		frappe.throw(_("Bay Management is disabled."))
	if booking_time in (None, ""):
		frappe.throw(_("A start time is required when allocating a Bay."))
	bay_doc = frappe.get_doc("Bay", bay)
	bay_doc.check_permission("read")
	if bay_doc.service_workshop != workshop:
		frappe.throw(_("The selected Bay does not belong to this Workshop."))
	# Serialize calendar allocation by Bay. Use current (locking) reads so a
	# transaction waiting here sees a concurrent booking after its commit.
	frappe.db.sql("SELECT name FROM `tabBay` WHERE name = %s FOR UPDATE", (bay,))
	# No duration field exists; do not claim to detect overlapping intervals.
	conflicts = frappe.db.sql(
		"""SELECT name FROM `tabService Booking`
			WHERE bay = %(bay)s AND booking_date = %(date)s
			AND booking_time = %(time)s AND status IN ('Pending', 'In Progress')
			AND docstatus < 2 AND name != %(exclude)s LIMIT 1 FOR UPDATE""",
		{"bay": bay, "date": booking_date, "time": booking_time, "exclude": exclude or ""},
	)
	if conflicts:
		frappe.throw(_("This Bay already has a booking at the selected start time."))


def _enrich(bookings):
	customer_names = sorted({row.customer for row in bookings if row.customer})
	vehicle_names = sorted({row.service_vehicle for row in bookings if row.service_vehicle})
	can_read_customers = frappe.has_permission("Customer", "read")
	can_read_vehicles = frappe.has_permission("Service Vehicle", "read")
	customers = (
		{
			row.name: row.customer_name
			for row in frappe.get_list(
				"Customer",
				filters={"name": ["in", customer_names]},
				fields=["name", "customer_name"],
				page_length=len(customer_names),
			)
		}
		if customer_names and can_read_customers
		else {}
	)
	vehicles = (
		{
			row.name: row
			for row in frappe.get_list(
				"Service Vehicle",
				filters={"name": ["in", vehicle_names]},
				fields=["name", "registration_number", "vehicle_model"],
				page_length=len(vehicle_names),
			)
		}
		if vehicle_names and can_read_vehicles
		else {}
	)
	result = []
	for row in bookings:
		vehicle = vehicles.get(row.service_vehicle)
		result.append(
			{
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
			}
		)
	return result


@frappe.whitelist()
def get_calendar_bookings(
	from_date, to_date, workshop=None, vehicle=None, customer=None, status=None, search=None
):
	"""Return individually permission-filtered bookings and optional visible Bays."""
	start, end = _date_range(from_date, to_date)
	filters = {"booking_date": ["between", [start, end]], "docstatus": ["<", 2]}
	if workshop:
		filters["workshop"] = _text(workshop, "Workshop")
	if customer:
		filters["customer"] = _text(customer, "Customer")
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
		fields=[
			"name",
			"booking_date",
			"booking_time",
			"customer",
			"service_vehicle",
			"workshop",
			"bay",
			"status",
			"job_card",
		],
		order_by="booking_date asc, booking_time asc, creation asc",
		page_length=10001,
	)
	if len(bookings) > 10000:
		frappe.throw(_("Too many bookings. Select a shorter date range or filter the results."))

	result = _enrich(bookings)
	if search:
		result = [
			row
			for row in result
			if any(
				search in str(row.get(field) or "").casefold()
				for field in ("name", "customer", "customer_name", "registration_number", "service_vehicle")
			)
		]
	bay_management_enabled = _bay_enabled()
	bays = []
	if bay_management_enabled and frappe.has_permission("Bay", "read"):
		bay_filters = {"service_workshop": workshop} if workshop else {}
		bays = frappe.get_list(
			"Bay",
			fields=["name", "service_workshop"],
			filters=bay_filters,
			order_by="name asc",
			page_length=1000,
		)
	return {
		"bookings": result,
		"bay_management_enabled": bay_management_enabled,
		"bays": bays,
		"timezone": get_system_timezone(),
		"can_create": bool(frappe.has_permission("Service Booking", "create")),
		"can_write": bool(frappe.has_permission("Service Booking", "write")),
	}


@frappe.whitelist()
def get_calendar_workshops(start=0):
	"""Page through readable Workshops without requiring access to load bookings."""
	frappe.has_permission("Service Booking", "read", throw=True)
	if not frappe.has_permission("Service Workshop", "read"):
		return []
	return frappe.get_list(
		"Service Workshop",
		fields=["name"],
		order_by="name asc",
		offset=max(0, cint(start)),
		limit=500,
	)


def _customer_required_fields():
	"""Expose editable required fields from the site's actual Customer metadata."""
	known = {"customer_name", "customer_type", "customer_group", "territory"}
	return [
		{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype, "options": f.options or ""}
		for f in frappe.get_meta("Customer").fields
		if f.reqd
		and not f.read_only
		and f.fieldname not in known
		and f.fieldtype in ("Data", "Select", "Link", "Int", "Float", "Date", "Phone")
	]


@frappe.whitelist()
def get_booking_context():
	if not (
		frappe.has_permission("Service Booking", "read") or frappe.has_permission("Service Booking", "create")
	):
		frappe.throw(_("You do not have permission to access bookings."), frappe.PermissionError)
	return {
		"bay_management_enabled": _bay_enabled(),
		"timezone": get_system_timezone(),
		"can_create_customer": bool(frappe.has_permission("Customer", "create")),
		"can_create_vehicle": bool(frappe.has_permission("Service Vehicle", "create")),
		"customer_required_fields": _customer_required_fields(),
	}


@frappe.whitelist(methods=["POST"])
def create_booking(booking, new_customer=None, new_vehicle=None):
	"""Create a booking and optional new customer/vehicle in one DB transaction."""
	values = _as_values(
		booking,
		(
			"customer",
			"service_vehicle",
			"booking_date",
			"booking_time",
			"workshop",
			"bay",
			"service_description",
		),
	)
	_date_range(values.get("booking_date"), values.get("booking_date"))
	values["booking_time"] = _time(values.get("booking_time"))
	if not values.get("workshop"):
		frappe.throw(_("Workshop is required."))
	frappe.has_permission("Service Booking", "create", throw=True)
	frappe.get_doc("Service Workshop", values["workshop"]).check_permission("read")
	_validate_bay(values.get("bay"), values["workshop"], values["booking_date"], values["booking_time"])

	if new_customer is not None:
		customer = _as_values(
			new_customer,
			(
				"customer_name",
				"customer_type",
				"customer_group",
				"territory",
				"tax_id",
				"mobile_no",
				*[f["fieldname"] for f in _customer_required_fields()],
			),
		)
		values["customer"] = frappe.get_doc({"doctype": "Customer", **customer}).insert().name
	if not values.get("customer"):
		frappe.throw(_("Customer is required."))
	frappe.get_doc("Customer", values["customer"]).check_permission("read")

	if new_vehicle is not None:
		vehicle = _as_values(
			new_vehicle,
			("registration_number", "vehicle_model", "engine_number", "chassis_number"),
		)
		if not vehicle.get("vehicle_model"):
			frappe.throw(_("Vehicle Model is required."))
		frappe.get_doc("Vehicle Model", vehicle["vehicle_model"]).check_permission("read")
		values["service_vehicle"] = (
			frappe.get_doc(
				{
					"doctype": "Service Vehicle",
					**vehicle,
					"customer": values["customer"],
				}
			)
			.insert()
			.name
		)
	if not values.get("service_vehicle"):
		frappe.throw(_("Service Vehicle is required."))
	vehicle_doc = frappe.get_doc("Service Vehicle", values["service_vehicle"])
	vehicle_doc.check_permission("read")
	if vehicle_doc.customer != values["customer"]:
		frappe.throw(_("The selected Vehicle does not belong to the Customer."))

	return frappe.get_doc({"doctype": "Service Booking", **values}).insert().as_dict()


@frappe.whitelist(methods=["POST"])
def reschedule_booking(name, booking_date, booking_time="", bay=None):
	"""Change pending bookings only, using the existing document validations."""
	_text(name, "Booking", limit=140)
	_date_range(booking_date, booking_date)
	booking_time = _time(booking_time)
	doc = frappe.get_doc("Service Booking", name, for_update=True)
	doc.check_permission("write")
	if doc.status != "Pending":
		frappe.throw(_("Only pending bookings can be rescheduled."))
	effective_bay = doc.bay if bay is None else _text(bay, "Bay", allow_empty=True)
	# Preserve historical Bay values when the feature is disabled.
	if _bay_enabled() or bay is not None:
		_validate_bay(effective_bay, doc.workshop, booking_date, booking_time, exclude=doc.name)

	doc.booking_date = booking_date
	doc.booking_time = booking_time
	if bay is not None:
		doc.bay = effective_bay
	doc.save()
	return {
		"name": doc.name,
		"booking_date": str(doc.booking_date),
		"booking_time": str(doc.booking_time or ""),
		"bay": doc.bay,
	}


@frappe.whitelist()
def get_calendar_holidays(from_date, to_date, workshop=None):
	"""Return the configured company Holiday List for booking-calendar display.

	Only the company's configured default list is exposed, and only to users
	with Service Booking read access. No arbitrary Holiday List can be queried.
	"""
	start, end = _date_range(from_date, to_date)
	frappe.has_permission("Service Booking", "read", throw=True)

	company = None
	if workshop:
		workshop_name = _text(workshop, "Workshop")
		visible = frappe.get_list(
			"Service Workshop", filters={"name": workshop_name}, fields=["name", "company"], page_length=1
		)
		if not visible:
			return {"holiday_list": None, "holidays": []}
		company = visible[0].company
	else:
		company = frappe.db.get_single_value("Service Settings", "company")

	if not company:
		return {"holiday_list": None, "holidays": []}
	holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
	if not holiday_list:
		return {"holiday_list": None, "holidays": []}

	rows = frappe.get_all(
		"Holiday",
		filters={
			"parenttype": "Holiday List",
			"parent": holiday_list,
			"holiday_date": ["between", [start, end]],
		},
		fields=["holiday_date", "description", "weekly_off", "is_half_day"],
		order_by="holiday_date asc",
		page_length=400,
	)
	holidays = [
		{
			"date": str(row.holiday_date),
			"description": strip_html_tags(row.description or "").strip()[:140] or _("Holiday"),
			"weekly_off": bool(row.weekly_off),
			"is_half_day": bool(row.is_half_day),
		}
		for row in rows
	]
	return {"holiday_list": holiday_list, "holidays": holidays}


def sync_calendar_navigation():
	"""Point only the calendar entry at the native Page, preserving site navigation."""
	if not frappe.db.exists("Page", "service-booking-calendar"):
		return {}
	from servicems.navigation import _navigation_write

	result = {}
	for doctype, name, table, type_field in (
		("Sidebar", "Service Management", "items", "link_type"),
		("Workspace", "Service MS", "shortcuts", "type"),
	):
		if not frappe.db.exists(doctype, name):
			continue
		doc = frappe.get_doc(doctype, name)
		changed = False
		for row in doc.get(table):
			if row.label != "Booking Calendar":
				continue
			if row.get(type_field) != "Page" or row.link_to != "service-booking-calendar" or row.url:
				row.set(type_field, "Page")
				row.link_to = "service-booking-calendar"
				row.url = ""
				changed = True
		if changed:
			with _navigation_write():
				doc.save(ignore_permissions=True)
		result[doctype] = changed
	return result
