# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe

from servicems.service_management.doctype.service_job_card import service_job_card_dashboard
from servicems.service_management.doctype.service_job_card.service_job_card import (
	get_all_supplied_parts,
	get_item_price,
	get_selected_items,
)
from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	COMPANY,
	CUSTOMER,
	CUSTOMER_PART_RATE,
	CUSTOMER_PRICE_LIST,
	CUSTOMER_WITH_PRICE_LIST,
	FREE_SERVICE_TEMPLATE,
	IGNORE_TEST_RECORD_DEPENDENCIES,
	PART_ITEM,
	PART_ITEM_2,
	PART_RATE,
	PART_RATE_2,
	PARTS_WAREHOUSE,
	PRICE_LIST,
	SERVICE_ITEM,
	SERVICE_RATE,
	SERVICE_TEMPLATE,
	TASK_A,
	TASK_B,
	TEMPLATE_PART_QTY,
	VEHICLE_2,
	VEHICLE_MAKE,
	VEHICLE_MODEL,
	VEHICLE_TYPE,
	WORKSHOP_WAREHOUSE,
	complete_tasks,
	make_job_card,
	receive_stock,
)

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES

TEMPLATE_SPARES_COST = PART_RATE * TEMPLATE_PART_QTY


def set_use_parts_entry(value):
	frappe.db.set_value("Company Service Management Settings", COMPANY, "use_parts_entry", value)


def submit_completed_job_card(**kwargs):
	job_card = make_job_card(**kwargs)
	complete_tasks(job_card)
	job_card.save()
	job_card.submit()
	return job_card


class TestServiceJobCardValidation(ServiceMSTestCase):
	def test_template_tasks_and_parts_are_applied(self):
		job_card = make_job_card()
		self.assertEqual([task.task_name for task in job_card.tasks], [TASK_A, TASK_B])
		self.assertEqual(job_card.tasks[0].template, SERVICE_TEMPLATE)
		self.assertEqual(len(job_card.parts), 1)
		part = job_card.parts[0]
		self.assertEqual(
			(part.item, part.qty, part.rate, part.is_billable), (PART_ITEM, TEMPLATE_PART_QTY, PART_RATE, 1)
		)
		service = job_card.services[0]
		self.assertEqual((service.item, service.applied, service.is_billable), (SERVICE_ITEM, 1, 1))

	def test_templates_are_applied_once(self):
		job_card = make_job_card()
		job_card.save()
		job_card.reload()
		self.assertEqual(len(job_card.tasks), 2)
		self.assertEqual(len(job_card.parts), 1)

	def test_bypass_billable_keeps_manual_flag(self):
		job_card = make_job_card(insert=False)
		job_card.services[0].update({"bypass_billable": 1, "is_billable": 0})
		job_card.insert()
		self.assertEqual(job_card.services[0].is_billable, 0)
		self.assertEqual(job_card.service_charges, 0)
		self.assertEqual(len(job_card.tasks), 2)

	def test_totals(self):
		job_card = make_job_card()
		self.assertEqual(job_card.service_charges, SERVICE_RATE)
		self.assertEqual(job_card.spares_cost, TEMPLATE_SPARES_COST)
		self.assertEqual(job_card.total, SERVICE_RATE + TEMPLATE_SPARES_COST)

	def test_non_billable_service_is_not_charged(self):
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE,))
		self.assertEqual(job_card.services[0].is_billable, 0)
		self.assertEqual(job_card.service_charges, 0)
		self.assertEqual(job_card.total, 0)
		self.assertEqual([task.task_name for task in job_card.tasks], [TASK_A])

	def test_non_billable_part_is_not_charged(self):
		parts = [{"item": PART_ITEM_2, "qty": 3, "rate": PART_RATE_2, "is_billable": 0}]
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE,), parts=parts)
		self.assertEqual(job_card.spares_cost, 0)

	def test_customer_price_list_takes_precedence(self):
		job_card = make_job_card(customer=CUSTOMER_WITH_PRICE_LIST, vehicle=VEHICLE_2)
		self.assertEqual(job_card.get_price_list(), CUSTOMER_PRICE_LIST)
		self.assertEqual(job_card.parts[0].rate, CUSTOMER_PART_RATE)

	def test_price_list_fallback_order(self):
		job_card = make_job_card()
		self.assertEqual(job_card.get_price_list(), PRICE_LIST)
		self.assertEqual(job_card.get_price_list("_Test Template PL"), "_Test Template PL")
		frappe.db.set_single_value("Service Settings", "price_list", None)
		self.assertEqual(job_card.get_price_list(), "")

	def test_get_item_price(self):
		self.assertEqual(get_item_price(PART_ITEM, PRICE_LIST, COMPANY), PART_RATE)
		self.assertEqual(get_item_price(PART_ITEM, "_Test Missing Price List", COMPANY), 0)

	def test_manual_part_rate_is_filled_from_price_list(self):
		parts = [
			{"item": PART_ITEM_2, "qty": 1, "is_billable": 1},
			{"item": PART_ITEM_2, "qty": 1, "rate": 5, "is_billable": 1},
		]
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE,), parts=parts)
		self.assertEqual(job_card.parts[0].rate, PART_RATE_2)
		self.assertEqual(job_card.parts[1].rate, 5)
		self.assertEqual(job_card.spares_cost, PART_RATE_2 + 5)

	def test_company_comes_from_service_settings(self):
		other_company = frappe.db.get_value("Company", {"name": ["!=", COMPANY]})
		job_card = make_job_card(company=other_company)
		self.assertEqual(job_card.company, COMPANY)

	def test_fetch_from_vehicle_and_workshop(self):
		job_card = make_job_card()
		self.assertEqual(job_card.customer, CUSTOMER)
		self.assertEqual(
			(job_card.vehicle_model, job_card.make, job_card.type),
			(VEHICLE_MODEL, VEHICLE_MAKE, VEHICLE_TYPE),
		)
		self.assertEqual(
			(job_card.engine_number, job_card.chassis_number, job_card.vin), ("ENG-001", "CH-001", "VIN-001")
		)
		self.assertEqual(job_card.mobile_no, "0700000001")

	def test_completed_requires_all_tasks_done(self):
		job_card = make_job_card()
		job_card.status = "Completed"
		self.assertRaisesRegex(frappe.ValidationError, "not Completed", job_card.save)
		job_card.reload()
		complete_tasks(job_card)
		job_card.save()
		self.assertEqual(job_card.status, "Completed")

	def test_submit_requires_completed_status(self):
		set_use_parts_entry(1)
		job_card = make_job_card(status="Active")
		self.assertRaisesRegex(frappe.ValidationError, "not completed", job_card.submit)

	def test_naming_series_and_website_route(self):
		job_card = make_job_card()
		self.assertRegex(job_card.name, r"^SJC-\d{2}-\d{6}$")
		self.assertEqual(job_card.route, f"job-card/{job_card.name.lower()}")
		self.assertEqual(frappe.db.get_value("Service Job Card", job_card.name, "route"), job_card.route)

	def test_complains_are_mandatory(self):
		doc = make_job_card(insert=False)
		doc.complains = []
		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_dashboard_links_stock_entry(self):
		data = service_job_card_dashboard.get_data()
		self.assertEqual(data["non_standard_fieldname"]["Stock Entry"], "service_job_card")
		self.assertTrue(frappe.get_meta("Stock Entry").has_field("service_job_card"))


class TestServiceJobCardStock(ServiceMSTestCase):
	def setUp(self):
		super().setUp()
		receive_stock(PART_ITEM)
		receive_stock(PART_ITEM_2)

	def test_submit_creates_stock_entry_and_invoice(self):
		set_use_parts_entry(0)
		job_card = submit_completed_job_card()

		self.assertEqual(len(job_card.parts), 0)
		self.assertEqual(len(job_card.supplied_parts), 1)
		supplied = job_card.supplied_parts[0]
		self.assertEqual(
			(supplied.item, supplied.qty, supplied.rate, supplied.is_billable),
			(PART_ITEM, TEMPLATE_PART_QTY, PART_RATE, 1),
		)

		stock_entry = frappe.get_doc("Stock Entry", supplied.stock_entry)
		self.assertEqual(stock_entry.docstatus, 1)
		self.assertEqual(stock_entry.purpose, "Material Transfer")
		self.assertEqual(stock_entry.service_job_card, job_card.name)
		self.assertEqual(
			(stock_entry.from_warehouse, stock_entry.to_warehouse), (PARTS_WAREHOUSE, WORKSHOP_WAREHOUSE)
		)
		self.assertEqual(stock_entry.items[0].qty, TEMPLATE_PART_QTY)

		invoice = frappe.get_doc("Sales Invoice", job_card.invoice)
		self.assertEqual(invoice.docstatus, 0)
		self.assertEqual((invoice.customer, invoice.company, invoice.update_stock), (CUSTOMER, COMPANY, 1))
		self.assertEqual(invoice.service_job_card, job_card.name)
		self.assertEqual(invoice.set_warehouse, WORKSHOP_WAREHOUSE)
		items = {row.item_code: row for row in invoice.items}
		self.assertEqual(set(items), {SERVICE_ITEM, PART_ITEM})
		self.assertEqual((items[SERVICE_ITEM].qty, items[SERVICE_ITEM].rate), (1, SERVICE_RATE))
		self.assertEqual((items[PART_ITEM].qty, items[PART_ITEM].rate), (TEMPLATE_PART_QTY, PART_RATE))
		self.assertTrue(invoice.taxes_and_charges)
		self.assertEqual(invoice.net_total, SERVICE_RATE + TEMPLATE_SPARES_COST)

	def test_invoice_without_default_tax_template(self):
		set_use_parts_entry(0)
		frappe.db.set_value(
			"Sales Taxes and Charges Template", {"company": COMPANY, "is_default": 1}, "is_default", 0
		)
		job_card = submit_completed_job_card()
		invoice = frappe.get_doc("Sales Invoice", job_card.invoice)
		self.assertFalse(invoice.taxes_and_charges)
		self.assertEqual(invoice.grand_total, SERVICE_RATE + TEMPLATE_SPARES_COST)

	def test_submit_with_parts_entry_setting_skips_stock_and_invoice(self):
		set_use_parts_entry(1)
		job_card = submit_completed_job_card()
		self.assertEqual(len(job_card.parts), 1)
		self.assertEqual(len(job_card.supplied_parts), 0)
		self.assertFalse(job_card.invoice)
		self.assertFalse(frappe.db.exists("Stock Entry", {"service_job_card": job_card.name}))

	def test_create_stock_entry_skips_rows_without_qty(self):
		parts = [{"item": PART_ITEM_2, "qty": 0, "rate": PART_RATE_2, "is_billable": 1}]
		job_card = make_job_card(parts=parts)
		job_card.create_stock_entry("call")
		job_card.reload()
		self.assertEqual([row.item for row in job_card.parts], [PART_ITEM_2])
		self.assertEqual([row.item for row in job_card.supplied_parts], [PART_ITEM])
		self.assertTrue(job_card.supplied_parts[0].stock_entry)

	def test_create_stock_entry_without_parts_is_noop(self):
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE,))
		job_card.create_stock_entry("call")
		self.assertEqual(len(job_card.supplied_parts), 0)

	def test_create_parts_entry(self):
		job_card = make_job_card()
		job_card.create_parts_entry("call")
		job_card.reload()

		part = job_card.parts[0]
		self.assertTrue(part.service_parts_entry)
		entry = frappe.get_doc("Service Parts Entry", part.service_parts_entry)
		self.assertEqual(entry.docstatus, 1)
		self.assertEqual((entry.company, entry.service_job_card), (COMPANY, job_card.name))
		self.assertEqual(
			(entry.items[0].item_code, entry.items[0].qty, entry.items[0].basic_rate),
			(PART_ITEM, TEMPLATE_PART_QTY, PART_RATE),
		)
		self.assertEqual(len(job_card.supplied_parts), 1)
		self.assertEqual(job_card.supplied_parts[0].item, PART_ITEM)

		self.assertRaisesRegex(frappe.ValidationError, "not available", job_card.create_parts_entry, "call")

	def test_create_parts_entry_without_parts(self):
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE,))
		self.assertRaisesRegex(frappe.ValidationError, "Add Parts", job_card.create_parts_entry, "call")

	def test_create_parts_entry_skips_existing_spares(self):
		parts = [{"item": PART_ITEM_2, "qty": 1, "use_existing_spares": 1, "is_billable": 1}]
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE,), parts=parts)
		self.assertRaisesRegex(frappe.ValidationError, "not available", job_card.create_parts_entry, "call")


def transferred_job_card():
	job_card = make_job_card()
	job_card.create_stock_entry("call")
	job_card.reload()
	return job_card


def return_rows(job_card, qty_to_return):
	rows = get_all_supplied_parts(job_card.name)
	for row in rows:
		row["qty_to_return"] = qty_to_return
	return frappe.as_json(rows)


class TestServiceJobCardReturns(ServiceMSTestCase):
	def setUp(self):
		super().setUp()
		receive_stock(PART_ITEM)

	def test_get_all_supplied_parts(self):
		job_card = transferred_job_card()
		rows = get_all_supplied_parts(job_card.name)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["item"], PART_ITEM)
		self.assertEqual(rows[0]["parenttype"], "Service Job Card")
		self.assertEqual(rows[0]["parent"], job_card.name)

		frappe.db.set_value("Supplied Parts", job_card.supplied_parts[0].name, "is_return", 1)
		self.assertEqual(get_all_supplied_parts(job_card.name), [])

	def test_partial_return(self):
		job_card = transferred_job_card()
		get_selected_items(return_rows(job_card, 1))
		job_card.reload()
		row = job_card.supplied_parts[0]
		self.assertEqual(
			(row.qty, row.qty_returned, row.is_return, row.is_billable), (TEMPLATE_PART_QTY - 1, 1, 0, 1)
		)
		return_entry = frappe.get_doc("Stock Entry", row.return_stock_enty)
		self.assertEqual(return_entry.docstatus, 1)
		self.assertEqual(
			(return_entry.from_warehouse, return_entry.to_warehouse), (WORKSHOP_WAREHOUSE, PARTS_WAREHOUSE)
		)
		self.assertEqual(return_entry.items[0].qty, 1)
		self.assertEqual(return_entry.service_job_card, job_card.name)
		self.assertEqual(job_card.spares_cost, PART_RATE * (TEMPLATE_PART_QTY - 1))

	def test_full_return_unbills_row(self):
		job_card = transferred_job_card()
		get_selected_items(return_rows(job_card, TEMPLATE_PART_QTY))
		job_card.reload()
		row = job_card.supplied_parts[0]
		self.assertEqual(
			(row.qty, row.qty_returned, row.is_return, row.is_billable), (0, TEMPLATE_PART_QTY, 1, 0)
		)
		self.assertEqual(job_card.spares_cost, 0)

	def test_return_requires_quantity(self):
		job_card = transferred_job_card()
		self.assertRaisesRegex(
			frappe.ValidationError, "empty quantity", get_selected_items, return_rows(job_card, 0)
		)


class TestServiceJobCardPermissions(ServiceMSTestCase):
	def test_only_system_manager_has_access(self):
		user = "_test_sms_sales@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": user,
					"first_name": "SMS Sales",
					"roles": [{"role": "Sales User"}],
				}
			).insert(ignore_permissions=True)
		self.assertFalse(frappe.has_permission("Service Job Card", "read", user=user))
		self.assertFalse(frappe.has_permission("Service Booking", "read", user=user))
		self.assertTrue(frappe.has_permission("Service Job Card", "submit", user="Administrator"))

	def test_stock_user_can_submit_parts_entry(self):
		user = "_test_sms_stock@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": user,
					"first_name": "SMS Stock",
					"roles": [{"role": "Stock User"}],
				}
			).insert(ignore_permissions=True)
		self.assertTrue(frappe.has_permission("Service Parts Entry", "submit", user=user))
		self.assertFalse(frappe.has_permission("Service Job Card", "read", user=user))
