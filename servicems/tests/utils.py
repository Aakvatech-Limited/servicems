"""Shared, idempotent fixtures for servicems tests. Every record uses a `_Test SMS` prefix."""

import frappe
from frappe.utils import add_days, now_datetime, nowdate

COMPANY = "_Test ServiceMS Co"
ABBR = "_TSC"
CURRENCY = "USD"
PARTS_WAREHOUSE = f"_Test SMS Parts - {ABBR}"
WORKSHOP_WAREHOUSE = f"_Test SMS Workshop - {ABBR}"
PRICE_LIST = "_Test SMS Price List"
CUSTOMER_PRICE_LIST = "_Test SMS Customer Price List"
CUSTOMER = "_Test SMS Customer"
CUSTOMER_WITH_PRICE_LIST = "_Test SMS Customer PL"
PARTS_ITEM_GROUP = "_Test SMS Parts"
SERVICES_ITEM_GROUP = "_Test SMS Services"
SERVICE_ITEM = "_Test SMS Service"
FREE_SERVICE_ITEM = "_Test SMS Free Service"
PART_ITEM = "_Test SMS Part"
PART_ITEM_2 = "_Test SMS Part 2"
WORKSHOP = "_Test SMS Workshop"
BAY = "_Test SMS Bay 1"
BAY_2 = "_Test SMS Bay 2"
VEHICLE_MAKE = "_Test SMS Make"
VEHICLE_TYPE = "_Test SMS Type"
VEHICLE_MODEL = "_Test SMS Model"
SOLD_BY = "_Test SMS Dealer"
VEHICLE = "_TSMS 001"
VEHICLE_2 = "_TSMS 002"
TASK_A = "_Test SMS Task A"
TASK_B = "_Test SMS Task B"
SERVICE_TEMPLATE = "_Test SMS Template"
FREE_SERVICE_TEMPLATE = "_Test SMS Free Template"
TAX_TEMPLATE = f"_Test SMS Taxes - {ABBR}"
TAX_ACCOUNT = f"_Test SMS VAT - {ABBR}"

SERVICE_RATE = 100.0
PART_RATE = 25.0
PART_RATE_2 = 40.0
CUSTOMER_PART_RATE = 30.0
TEMPLATE_PART_QTY = 2
STOCK_VALUATION_RATE = 20.0

# Prunes frappe's automatic test-record generation for ERPNext doctypes linked from servicems.
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Company",
	"Warehouse",
	"Customer",
	"Item",
	"Item Group",
	"Price List",
	"UOM",
	"Brand",
	"Sales Invoice",
	"Stock Entry",
	"Quotation",
	"Department",
	"Print Heading",
	"Letter Head",
	"User",
]


def create_test_data():
	"""Create every record the servicems tests need and commit them."""
	frappe.set_user("Administrator")  # nosemgrep
	create_company()
	create_warehouses()
	create_item_groups()
	create_items()
	create_price_lists()
	create_customers()
	create_tax_template()
	create_service_settings()
	create_company_settings()
	create_workshop()
	create_bays()
	create_vehicle_masters()
	create_vehicles()
	create_service_templates()
	frappe.db.commit()  # nosemgrep


def create_company():
	if frappe.db.exists("Company", COMPANY):
		return
	frappe.db.set_value("Currency", CURRENCY, "enabled", 1)
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": COMPANY,
			"abbr": ABBR,
			"default_currency": CURRENCY,
			"country": "United States",
			"chart_of_accounts": "Standard",
			"valuation_method": "FIFO",
		}
	).insert()


def create_warehouses():
	for name in ("_Test SMS Parts", "_Test SMS Workshop"):
		if not frappe.db.exists("Warehouse", f"{name} - {ABBR}"):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": name, "company": COMPANY}).insert()


def create_item_groups():
	for name in (PARTS_ITEM_GROUP, SERVICES_ITEM_GROUP):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc(
				{"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups"}
			).insert()


def create_items():
	items = [
		(SERVICE_ITEM, SERVICES_ITEM_GROUP, 0),
		(FREE_SERVICE_ITEM, SERVICES_ITEM_GROUP, 0),
		(PART_ITEM, PARTS_ITEM_GROUP, 1),
		(PART_ITEM_2, PARTS_ITEM_GROUP, 1),
	]
	for item_code, item_group, is_stock_item in items:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_code,
				"item_group": item_group,
				"stock_uom": "Nos",
				"is_stock_item": is_stock_item,
				"valuation_rate": STOCK_VALUATION_RATE if is_stock_item else 0,
			}
		).insert()


def create_price_lists():
	prices = {
		PRICE_LIST: [(SERVICE_ITEM, SERVICE_RATE), (PART_ITEM, PART_RATE), (PART_ITEM_2, PART_RATE_2)],
		CUSTOMER_PRICE_LIST: [(SERVICE_ITEM, SERVICE_RATE), (PART_ITEM, CUSTOMER_PART_RATE)],
	}
	for price_list, item_prices in prices.items():
		if not frappe.db.exists("Price List", price_list):
			frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": price_list,
					"currency": CURRENCY,
					"selling": 1,
					"enabled": 1,
				}
			).insert()
		for item_code, rate in item_prices:
			if frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list}):
				continue
			frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": item_code,
					"price_list": price_list,
					"price_list_rate": rate,
				}
			).insert()


def create_customers():
	customers = [(CUSTOMER, None), (CUSTOMER_WITH_PRICE_LIST, CUSTOMER_PRICE_LIST)]
	for name, default_price_list in customers:
		if frappe.db.exists("Customer", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}),
				"territory": frappe.db.get_value("Territory", {"is_group": 0}),
				"default_price_list": default_price_list,
				"mobile_no": "0700000001",
			}
		).insert()


def create_tax_template():
	if frappe.db.exists("Sales Taxes and Charges Template", TAX_TEMPLATE):
		return
	if not frappe.db.exists("Account", TAX_ACCOUNT):
		parent = frappe.db.get_value(
			"Account", {"company": COMPANY, "account_name": "Duties and Taxes", "is_group": 1}
		) or frappe.db.get_value("Account", {"company": COMPANY, "root_type": "Liability", "is_group": 1})
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": "_Test SMS VAT",
				"parent_account": parent,
				"company": COMPANY,
				"account_type": "Tax",
			}
		).insert()
	frappe.get_doc(
		{
			"doctype": "Sales Taxes and Charges Template",
			"title": "_Test SMS Taxes",
			"company": COMPANY,
			"is_default": 1,
			"taxes": [
				{
					"charge_type": "On Net Total",
					"account_head": TAX_ACCOUNT,
					"description": "VAT",
					"rate": 18,
				}
			],
		}
	).insert()


def create_service_settings():
	settings = frappe.get_doc("Service Settings")
	settings.company = COMPANY
	settings.price_list = PRICE_LIST
	settings.default_is_billable = 1
	settings.item_groups = []
	settings.append("item_groups", {"item_group": PARTS_ITEM_GROUP})
	settings.save()


def create_company_settings(use_parts_entry=0):
	if frappe.db.exists("Company Service Management Settings", COMPANY):
		frappe.db.set_value(
			"Company Service Management Settings", COMPANY, "use_parts_entry", use_parts_entry
		)
		return
	frappe.get_doc(
		{
			"doctype": "Company Service Management Settings",
			"company": COMPANY,
			"use_parts_entry": use_parts_entry,
		}
	).insert()


def create_workshop():
	if frappe.db.exists("Service Workshop", WORKSHOP):
		return
	frappe.get_doc(
		{
			"doctype": "Service Workshop",
			"workshop_name": WORKSHOP,
			"company": COMPANY,
			"parts_warehouse": PARTS_WAREHOUSE,
			"workshop_warehouse": WORKSHOP_WAREHOUSE,
		}
	).insert()


def create_bays():
	for bay in (BAY, BAY_2):
		if not frappe.db.exists("Bay", bay):
			frappe.get_doc({"doctype": "Bay", "bay": bay, "service_workshop": WORKSHOP}).insert()


def create_vehicle_masters():
	if not frappe.db.exists("Vehicle Make", VEHICLE_MAKE):
		frappe.get_doc({"doctype": "Vehicle Make", "make": VEHICLE_MAKE}).insert()
	if not frappe.db.exists("Service Vehicle Type", VEHICLE_TYPE):
		frappe.get_doc({"doctype": "Service Vehicle Type", "vehicle_type": VEHICLE_TYPE}).insert()
	if not frappe.db.exists("Vehicle Model", VEHICLE_MODEL):
		frappe.get_doc(
			{
				"doctype": "Vehicle Model",
				"model_name": VEHICLE_MODEL,
				"make": VEHICLE_MAKE,
				"type": VEHICLE_TYPE,
			}
		).insert()
	if not frappe.db.exists("Sold By", SOLD_BY):
		frappe.get_doc({"doctype": "Sold By", "sold_by": SOLD_BY}).insert()


def create_vehicles():
	vehicles = [(VEHICLE, CUSTOMER), (VEHICLE_2, CUSTOMER_WITH_PRICE_LIST)]
	for registration_number, customer in vehicles:
		if frappe.db.exists("Service Vehicle", registration_number):
			continue
		frappe.get_doc(
			{
				"doctype": "Service Vehicle",
				"registration_number": registration_number,
				"customer": customer,
				"vehicle_model": VEHICLE_MODEL,
				"engine_number": "ENG-001",
				"chassis_number": "CH-001",
				"vin": "VIN-001",
				"sold_by": SOLD_BY,
				"recommended_service_interval": "5000",
			}
		).insert()


def create_service_templates():
	for task in (TASK_A, TASK_B):
		if not frappe.db.exists("Service Task", task):
			frappe.get_doc({"doctype": "Service Task", "task_name": task}).insert()
	if not frappe.db.exists("Service Template", SERVICE_TEMPLATE):
		frappe.get_doc(
			{
				"doctype": "Service Template",
				"template_name": SERVICE_TEMPLATE,
				"item": SERVICE_ITEM,
				"is_billable": 1,
				"tasks": [{"task_name": TASK_A}, {"task_name": TASK_B}],
				"parts": [{"item": PART_ITEM, "qty": TEMPLATE_PART_QTY, "is_billable": 1}],
			}
		).insert()
	if not frappe.db.exists("Service Template", FREE_SERVICE_TEMPLATE):
		frappe.get_doc(
			{
				"doctype": "Service Template",
				"template_name": FREE_SERVICE_TEMPLATE,
				"item": FREE_SERVICE_ITEM,
				"is_billable": 0,
				"tasks": [{"task_name": TASK_A}],
			}
		).insert()


def receive_stock(item_code=PART_ITEM, qty=100, warehouse=PARTS_WAREHOUSE, batch_no=None):
	"""Book a Material Receipt so transfers and invoices have stock to consume."""
	row = {"item_code": item_code, "qty": qty, "t_warehouse": warehouse, "basic_rate": STOCK_VALUATION_RATE}
	if batch_no:
		row.update({"batch_no": batch_no, "use_serial_batch_fields": 1})
	entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": COMPANY,
			"to_warehouse": warehouse,
			"items": [row],
		}
	)
	entry.insert()
	entry.submit()
	return entry


def make_job_card(
	customer=CUSTOMER,
	vehicle=VEHICLE,
	services=(SERVICE_TEMPLATE,),
	parts=None,
	status="Initiated",
	insert=True,
	**kwargs,
):
	doc = frappe.get_doc(
		{
			"doctype": "Service Job Card",
			"workshop": WORKSHOP,
			"service_item_name": vehicle,
			"customer": customer,
			"receiving_datetime": now_datetime(),
			"status": status,
			"complains": [{"description": "Unusual noise"}],
			"services": [{"service": service} for service in services],
			"parts": parts or [],
			**kwargs,
		}
	)
	if insert:
		doc.insert()
	return doc


def complete_tasks(job_card):
	for task in job_card.tasks:
		task.completed = 1
	job_card.status = "Completed"
	return job_card


def make_booking(
	customer=CUSTOMER,
	vehicle=VEHICLE,
	bay=BAY,
	booking_date=None,
	booking_time="10:00:00",
	workshop=WORKSHOP,
	**kwargs,
):
	return frappe.get_doc(
		{
			"doctype": "Service Booking",
			"customer": customer,
			"service_vehicle": vehicle,
			"bay": bay,
			"workshop": workshop,
			"booking_date": booking_date or add_days(nowdate(), 1),
			"booking_time": booking_time,
			**kwargs,
		}
	).insert()
