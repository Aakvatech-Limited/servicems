"""Disposable real ERPNext transactions. Every test rolls back its own records."""

import base64
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from servicems.billing import make_invoice, make_quotation
from servicems.costing import get_costs
from servicems.parts import allocations, post_parts


class TestPhaseTwo(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.db.rollback)
		self.token = frappe.generate_hash(length=8)
		self.company = frappe.get_doc(
			dict(
				doctype="Company",
				company_name="Phase2 " + self.token,
				abbr=self.token,
				default_currency="TZS",
				country="Tanzania",
			)
		).insert()
		self.company.reload()
		self.expense = frappe.db.get_value(
			"Account", {"company": self.company.name, "is_group": 0, "root_type": "Expense"}, "name"
		)
		self.cost_center = frappe.db.get_value(
			"Cost Center", {"company": self.company.name, "is_group": 0}, "name"
		)
		self.stores = (
			frappe.get_doc(
				dict(doctype="Warehouse", warehouse_name="P2 Stores " + self.token, company=self.company.name)
			)
			.insert()
			.name
		)
		self.workshop_wh = (
			frappe.get_doc(
				dict(
					doctype="Warehouse", warehouse_name="P2 Workshop " + self.token, company=self.company.name
				)
			)
			.insert()
			.name
		)
		self.workshop = frappe.get_doc(
			dict(
				doctype="Service Workshop",
				workshop_name="P2 " + self.token,
				company=self.company.name,
				parts_warehouse=self.stores,
				workshop_warehouse=self.workshop_wh,
			)
		).insert()
		self.item = frappe.get_doc(
			dict(
				doctype="Item",
				item_code="P2-Part-" + self.token,
				item_name="Disposable Phase 2 part",
				item_group="All Item Groups",
				stock_uom="Nos",
				is_stock_item=1,
				valuation_rate=10,
			)
		).insert()
		self.tax_account = (
			frappe.get_doc(
				dict(
					doctype="Account",
					account_name="P2 VAT " + self.token,
					company=self.company.name,
					parent_account=frappe.db.get_value(
						"Account",
						{"company": self.company.name, "root_type": "Liability", "is_group": 1},
						"name",
					),
					account_type="Tax",
					root_type="Liability",
					report_type="Balance Sheet",
				)
			)
			.insert()
			.name
		)
		self.tax_template = (
			frappe.get_doc(
				dict(
					doctype="Item Tax Template",
					title="P2 VAT " + self.token,
					company=self.company.name,
					vfd_taxcode="1- Standard Rate (18%)",
					taxes=[dict(tax_type=self.tax_account, tax_rate=18)],
				)
			)
			.insert()
			.name
		)
		self.item.append(
			"taxes",
			dict(
				item_tax_template=self.tax_template, tax_category=frappe.new_doc("Sales Invoice").tax_category
			),
		)
		self.item.save()
		self.sales_tax = (
			frappe.get_doc(
				dict(
					doctype="Sales Taxes and Charges Template",
					title="P2 VAT " + self.token,
					company=self.company.name,
					is_default=1,
					taxes=[
						dict(
							charge_type="On Net Total",
							account_head=self.tax_account,
							description="VAT",
							rate=18,
						)
					],
				)
			)
			.insert()
			.name
		)
		self.customer = frappe.get_doc(
			dict(
				doctype="Customer",
				customer_name="P2 Customer " + self.token,
				customer_type="Company",
				customer_group=frappe.get_doc(
					dict(
						doctype="Customer Group",
						customer_group_name="P2 Group " + self.token,
						parent_customer_group="All Customer Groups",
						is_group=0,
					)
				)
				.insert()
				.name,
				territory="All Territories",
			)
		).insert()
		self.item.taxes[0].tax_category = self.customer.tax_category
		self.item.save()
		model = frappe.get_doc(dict(doctype="Vehicle Model", model_name="P2 Model " + self.token)).insert()
		vehicle = frappe.get_doc(
			dict(
				doctype="Service Vehicle",
				registration_number="P2-" + self.token,
				customer=self.customer.name,
				vehicle_model=model.name,
			)
		).insert()
		self.service_item = frappe.get_doc(
			dict(
				doctype="Item",
				item_code="P2-Service-" + self.token,
				item_name="Disposable repair service",
				item_group="All Item Groups",
				stock_uom="Nos",
				is_stock_item=0,
				taxes=[dict(item_tax_template=self.tax_template, tax_category=self.customer.tax_category)],
			)
		).insert()
		task = frappe.get_doc(dict(doctype="Service Task", task_name="P2 Task " + self.token)).insert()
		template = frappe.get_doc(
			dict(
				doctype="Service Template",
				template_name="P2 Service " + self.token,
				item=self.service_item.name,
				tasks=[dict(task_name=task.name)],
			)
		).insert()
		booking = frappe.get_doc(
			dict(
				doctype="Service Booking",
				customer=self.customer.name,
				service_vehicle=vehicle.name,
				booking_date=frappe.utils.nowdate(),
				workshop=self.workshop.name,
			)
		).insert()
		self.card = frappe.get_doc(
			dict(
				doctype="Service Job Card",
				company=self.company.name,
				workshop=self.workshop.name,
				customer=self.customer.name,
				service_item_name=vehicle.name,
				service_booking=booking.name,
				status="Active",
				expense_account=self.expense,
				cost_center=self.cost_center,
				internal_maintenance=1,
			)
		)
		self.card.append("parts", dict(item=self.item.name, qty=10, rate=20, is_billable=1))
		self.card.append("complains", dict(complain="Disposable maintenance test"))
		self.card.append("services", dict(service=template.name, item=self.service_item.name, is_billable=0))
		with patch.object(type(self.card), "set_company_from_service_settings"):
			self.card.insert()
		self.receipt = frappe.get_doc(
			dict(
				doctype="Stock Entry",
				stock_entry_type="Material Receipt",
				company=self.company.name,
				items=[
					dict(
						item_code=self.item.name,
						qty=30,
						t_warehouse=self.stores,
						basic_rate=10,
						expense_account=self.expense,
						cost_center=self.cost_center,
					)
				],
			)
		).insert()
		self.receipt.submit()

	def issue(self, qty=10, part=None):
		name = post_parts(
			self.card.name,
			"Issue",
			[{"part_row": part or self.card.parts[0].name, "qty": qty}],
			frappe.generate_hash(length=16),
		)
		return frappe.get_doc("Stock Entry", name)

	def move(self, operation, source, qty, request=None):
		return post_parts(
			self.card.name,
			operation,
			[{"issue_detail": source.items[0].name, "qty": qty}],
			request or frappe.generate_hash(length=16),
		)

	def test_stock_and_gl_lifecycle(self):
		source = self.issue()
		consume = self.move("Consume", source, 6)
		returned = self.move("Return", source, 4)
		bucket = allocations(self.card)[source.items[0].name]
		self.assertEqual(
			(bucket["issued"], bucket["consumed"], bucket["returned"], bucket["outstanding"]), (10, 6, 4, 0)
		)
		qty = frappe.db.sql(
			"select sum(actual_qty) from `tabStock Ledger Entry` where item_code=%s and warehouse=%s and is_cancelled=0",
			(self.item.name, self.workshop_wh),
		)[0][0]
		self.assertEqual(qty, 0)
		stock_value = frappe.db.sql(
			"select sum(stock_value_difference) from `tabStock Ledger Entry` where voucher_no=%s and is_cancelled=0",
			consume,
		)[0][0]
		self.assertEqual(stock_value, -60)
		gl = frappe.db.sql(
			"select sum(debit), sum(credit) from `tabGL Entry` where voucher_no=%s and is_cancelled=0",
			consume,
		)[0]
		self.assertEqual(tuple(gl), (60, 60))
		expense = frappe.db.sql(
			"select sum(debit-credit) from `tabGL Entry` where voucher_no=%s and account=%s and cost_center=%s and is_cancelled=0",
			(consume, self.expense, self.cost_center),
		)[0][0]
		self.assertEqual(expense, 60)
		self.assertEqual(get_costs(self.card)["actual_parts_cost"], 60)
		for transfer in (source.name, returned):
			self.assertFalse(
				frappe.db.sql(
					"select name from `tabGL Entry` where voucher_no=%s and account=%s and is_cancelled=0 and debit!=credit",
					(transfer, self.expense),
				)
			)

	def test_partial_duplicate_and_exceptions(self):
		source = self.issue()
		request = frappe.generate_hash(length=16)
		first = self.move("Consume", source, 3, request)
		self.assertEqual(self.move("Consume", source, 3, request), first)
		self.move("Return", source, 2)
		self.assertEqual(allocations(self.card)[source.items[0].name]["outstanding"], 5)
		for operation, qty in (("Consume", 6), ("Return", 6), ("Consume", -1), ("Return", 0)):
			with self.assertRaises(frappe.ValidationError):
				self.move(operation, source, qty)
		with self.assertRaises(frappe.ValidationError):
			self.issue()

	def test_cancellation_and_reversal(self):
		source = self.issue()
		consume = self.move("Consume", source, 4)
		with self.assertRaises(frappe.ValidationError):
			source.cancel()
		frappe.get_doc("Stock Entry", consume).cancel()
		self.assertEqual(allocations(self.card)[source.items[0].name]["outstanding"], 10)
		self.assertEqual(get_costs(self.card)["actual_parts_cost"], 0)
		source.reload().cancel()
		self.assertEqual(allocations(self.card), {})

	def test_multiple_issues_same_item(self):
		first = self.issue()
		self.card.append("parts", dict(item=self.item.name, qty=5, rate=20, is_billable=1))
		with patch.object(type(self.card), "set_company_from_service_settings"):
			self.card.save()
		second = frappe.get_doc("Stock Entry", self.card.create_stock_entry())
		self.assertIsNone(self.card.create_stock_entry())
		self.move("Consume", first, 4)
		self.move("Return", second, 2)
		buckets = allocations(self.card)
		self.assertEqual(buckets[first.items[0].name]["outstanding"], 6)
		self.assertEqual(buckets[second.items[0].name]["outstanding"], 3)

	def test_insufficient_stock(self):
		self.card.parts[0].qty = 100
		with patch.object(type(self.card), "set_company_from_service_settings"):
			self.card.save()
		with self.assertRaises(frappe.ValidationError):
			self.issue(100)

	def test_billing_does_not_consume_again(self):
		source = self.issue()
		self.move("Consume", source, 6)
		frappe.db.set_value("Service Job Card", self.card.name, "internal_maintenance", 0)
		frappe.get_doc("Quotation", make_quotation(self.card.name)).submit()
		invoice = frappe.get_doc("Sales Invoice", make_invoice(self.card.name))
		self.assertEqual(invoice.items[0].item_tax_template, self.tax_template)
		self.assertFalse(invoice.update_stock)
		self.assertEqual(invoice.items[0].qty, 6)
		invoice.submit()
		self.assertFalse(frappe.db.exists("Stock Ledger Entry", {"voucher_no": invoice.name}))
		self.assertEqual(get_costs(self.card)["parts_revenue"], 120)
		with self.assertRaises(frappe.ValidationError):
			make_invoice(self.card.name)
		invoice.cancel()
		self.assertEqual(get_costs(self.card)["parts_revenue"], 0)

	def test_template_snapshot_completion_and_correction(self):
		template = frappe.get_doc(
			dict(
				doctype="Service Pre Inspection Template",
				template_name="P2 Template " + self.token,
				pre_inspection_items=[
					dict(inspection_item="Lights", inspection_type="Check"),
					dict(inspection_item="Brakes", inspection_type="Data", require_photo=1),
				],
			)
		).insert()
		inspection = frappe.get_doc(
			dict(
				doctype="Service Vehicle Inspection",
				service_job_card=self.card.name,
				inspection_stage="Pre-Service",
				inspection_status="Draft",
				inspection_template=template.name,
			)
		).insert()
		self.assertEqual(len(inspection.checklist), 2)
		inspection.append(
			"service_lighting_checklist",
			dict(
				lighting_check_item="Headlamp", lighting_mark=1, lighting_remarks="Original detailed answer"
			),
		)
		inspection.save()
		template.pre_inspection_items[0].inspection_item = "Changed later"
		template.save()
		inspection.reload().save()
		self.assertEqual(inspection.checklist[0].inspection_item, "Lights")
		inspection.inspection_status = "Completed"
		with self.assertRaises(frappe.ValidationError):
			inspection.save()
		inspection.reload()
		inspection.inspection_status = "Completed"
		from frappe.utils.file_manager import save_file

		photo = save_file(
			"p2-" + self.token + ".png",
			base64.b64decode(
				"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a7WQAAAAASUVORK5CYII="
			),
			"Service Vehicle Inspection",
			inspection.name,
			is_private=1,
		)
		self.photo_url = photo.file_url
		self.addCleanup(lambda: Path(photo.get_full_path()).unlink(missing_ok=True))
		inspection.image_upload = self.photo_url
		with self.assertRaises(frappe.ValidationError):
			inspection.save()
		inspection.reload()
		inspection.inspection_status = "Completed"

		inspection.image_upload = self.photo_url
		inspection.checklist[1].photograph = self.photo_url
		inspection.save()
		self.assertEqual(inspection.completed_by, "Administrator")
		self.assertTrue(inspection.inspected_on)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc("File", photo.name).delete()
		self.assertTrue(Path(photo.get_full_path()).exists())
		with self.assertRaises(frappe.ValidationError):
			inspection.inspection_remarks = "silent change"
			inspection.save()
		correction = frappe.get_doc(
			"Service Vehicle Inspection", inspection.reload().create_correction("Correct brake result")
		)
		self.assertEqual(correction.inspection_status, "Draft")
		self.assertEqual(correction.corrects_inspection, inspection.name)
		self.assertEqual(len(correction.checklist), 2)
		self.assertEqual(
			correction.service_lighting_checklist[0].lighting_remarks, "Original detailed answer"
		)

	def test_concurrent_post_waits_for_job_card_lock(self):
		from concurrent.futures import ThreadPoolExecutor

		source = self.issue()
		site, sites_path, name, detail = (
			frappe.local.site,
			frappe.local.sites_path,
			self.card.name,
			source.items[0].name,
		)

		def competing_request():
			frappe.init(site, sites_path=sites_path)
			frappe.connect()
			frappe.set_user("Administrator")
			try:
				# Read the uncommitted disposable fixture only; posting must still wait
				# for its row lock. Nothing is committed for this contention test.
				frappe.db.sql("set session transaction isolation level read uncommitted")
				frappe.db.sql("set session innodb_lock_wait_timeout=1")
				try:
					post_parts(name, "Consume", [{"issue_detail": detail, "qty": 8}], "competing-request")
				except frappe.QueryTimeoutError:
					return "locked"
				return "unexpected-post"
			finally:
				frappe.db.rollback()
				frappe.destroy()

		with ThreadPoolExecutor(max_workers=1) as pool:
			self.assertEqual(pool.submit(competing_request).result(timeout=15), "locked")
		self.move("Consume", source, 8)
		with self.assertRaises(frappe.ValidationError):
			self.move("Consume", source, 8)
		self.assertEqual(allocations(self.card)[detail]["consumed"], 8)

	def test_separate_insurance_and_owner_receivables(self):
		source = self.issue()
		self.move("Consume", source, 6)
		insurer = frappe.copy_doc(self.customer)
		insurer.customer_name = "P2 Insurer " + self.token
		insurer.insert()
		self.card.reload()
		self.card.internal_maintenance = 0
		self.card.append(
			"payer_allocations", dict(customer=insurer.name, responsibility="Insurance", approved_amount=90)
		)
		self.card.append(
			"payer_allocations",
			dict(customer=self.customer.name, responsibility="Deductible", approved_amount=30),
		)
		self.card.flags.ignore_mandatory = True
		self.card.save()
		frappe.get_doc("Quotation", make_quotation(self.card.name)).submit()
		invoices = []
		for payer, amount in ((insurer.name, 90), (self.customer.name, 30)):
			invoice = frappe.get_doc("Sales Invoice", make_invoice(self.card.name, payer))
			self.assertEqual(invoice.net_total, amount)
			invoice.submit()
			self.assertEqual(invoice.outstanding_amount, invoice.rounded_total or invoice.grand_total)
			invoices.append(invoice)
		self.assertEqual(get_costs(self.card)["parts_revenue"], 120)
		self.assertEqual(sum(i.net_total for i in invoices), 120)
		self.assertEqual(allocations(self.card)[source.items[0].name]["consumed"], 6)

	def test_labour_and_internal_close_without_invoice(self):
		employee = frappe.get_doc(
			dict(
				doctype="Employee",
				first_name="Phase2 " + self.token,
				national_identity=self.token,
				gender="Male",
				date_of_birth="1990-01-01",
				date_of_joining="2026-01-01",
				company=self.company.name,
				status="Active",
			)
		).insert()
		source = self.issue()
		self.move("Consume", source, 7)
		self.move("Return", source, 3)
		self.card.reload()
		self.card.append(
			"labour_entries",
			dict(
				technician=employee.name,
				started_at="2026-11-01 09:00:00",
				stopped_at="2026-11-01 11:00:00",
				internal_cost_rate=25,
				customer_charge_rate=40,
				is_billable=0,
			),
		)
		for task in self.card.tasks:
			task.completed = 1
		self.card.status = "Completed"
		self.card.quality_check_confirmed = 1
		self.card.estimated_cost = 100
		self.card.costs_confirmed = 1
		self.card.flags.ignore_mandatory = True
		self.card.save()
		self.card.submit()
		costs = get_costs(self.card)
		self.assertEqual(costs["actual_labour_hours"], 2)
		self.assertEqual(costs["actual_labour_cost"], 50)
		self.assertEqual(costs["total_actual_cost"], 120)
		self.assertEqual(costs["cost_variance"], 20)
		self.assertFalse(frappe.db.exists("Sales Invoice", {"service_job_card": self.card.name}))

	def test_legacy_acceptance_migration_is_opt_in_and_idempotent(self):
		from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
			migrate_legacy_acceptance,
		)

		frappe.db.set_value(
			"Service Job Card", self.card.name, {"service_book": 1, "battery_make": "Historical battery"}
		)
		name = migrate_legacy_acceptance(self.card.name)
		self.assertEqual(migrate_legacy_acceptance(self.card.name), name)
		inspection = frappe.get_doc("Service Vehicle Inspection", name)
		self.assertEqual(inspection.inspection_status, "Draft")
		self.assertIn("Historical battery", [row.answer for row in inspection.checklist])
		self.assertEqual(
			frappe.db.get_value("Service Job Card", self.card.name, "battery_make"), "Historical battery"
		)

	def test_stock_posting_denies_guest(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				post_parts(
					self.card.name,
					"Issue",
					[{"part_row": self.card.parts[0].name, "qty": 10}],
					"guest-request",
				)
		finally:
			frappe.set_user("Administrator")

	def test_external_supplier_cost_and_reversal(self):
		supplier_group = frappe.get_doc(
			dict(
				doctype="Supplier Group",
				supplier_group_name="P2 Suppliers " + self.token,
				parent_supplier_group="All Supplier Groups",
				is_group=0,
			)
		).insert()
		supplier = frappe.get_doc(
			dict(
				doctype="Supplier",
				supplier_name="P2 Provider " + self.token,
				supplier_group=supplier_group.name,
				supplier_type="Company",
			)
		).insert()
		invoice = frappe.get_doc(
			dict(
				doctype="Purchase Invoice",
				company=self.company.name,
				supplier=supplier.name,
				bill_no="P2-" + self.token,
				bill_date=frappe.utils.nowdate(),
				items=[
					dict(
						item_code=self.service_item.name,
						qty=1,
						rate=35,
						service_job_card=self.card.name,
						expense_account=self.expense,
						cost_center=self.cost_center,
					)
				],
			)
		).insert()
		invoice.submit()
		self.assertEqual(get_costs(self.card)["external_service_cost"], 35)
		gl = frappe.db.sql(
			"select sum(debit-credit) from `tabGL Entry` where voucher_no=%s and account=%s and cost_center=%s and is_cancelled=0",
			(invoice.name, self.expense, self.cost_center),
		)[0][0]
		self.assertEqual(gl, 35)
		invoice.cancel()
		self.assertEqual(get_costs(self.card)["external_service_cost"], 0)

	def test_invoice_payment_reconciles_receivable(self):
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		source = self.issue()
		self.move("Consume", source, 4)
		self.move("Return", source, 6)
		frappe.db.set_value("Service Job Card", self.card.name, "internal_maintenance", 0)
		frappe.get_doc("Quotation", make_quotation(self.card.name)).submit()
		invoice = frappe.get_doc("Sales Invoice", make_invoice(self.card.name))
		invoice.submit()
		cash = frappe.db.get_value(
			"Account", {"company": self.company.name, "account_type": "Cash", "is_group": 0}, "name"
		)
		payment = get_payment_entry("Sales Invoice", invoice.name, bank_account=cash)
		payment.insert()
		payment.submit()
		self.assertEqual(invoice.reload().outstanding_amount, 0)
		balance = frappe.db.sql(
			"select sum(debit-credit) from `tabGL Entry` where company=%s and party_type='Customer' and party=%s and is_cancelled=0",
			(self.company.name, self.customer.name),
		)[0][0]
		self.assertEqual(balance, 0)
		self.card.reload()
		for task in self.card.tasks:
			task.completed = 1
		self.card.status = "Completed"
		self.card.quality_check_confirmed = 1
		self.card.save()
		self.card.submit()
		self.assertEqual(
			frappe.db.get_value("Service Booking", self.card.service_booking, "status"), "Completed"
		)

	def test_quotation_approval_and_supplement(self):
		frappe.db.set_value("Service Job Card", self.card.name, "internal_maintenance", 0)
		first = make_quotation(self.card.name)
		self.assertEqual(make_quotation(self.card.name), first)
		source = self.issue()
		self.move("Consume", source, 2)
		with self.assertRaises(frappe.ValidationError):
			make_invoice(self.card.name)
		frappe.get_doc("Quotation", first).submit()
		self.card.reload()
		self.card.append(
			"services",
			dict(
				service=self.card.services[0].service,
				item=self.service_item.name,
				is_billable=1,
				bypass_billable=1,
				applied=1,
				rate=30,
				charge_category="External Service",
			),
		)
		self.card.save()
		second = make_quotation(self.card.name)
		self.assertNotEqual(first, second)
		self.assertEqual(len(frappe.get_doc("Quotation", second).items), 1)
		frappe.get_doc("Quotation", second).submit()
		invoice = frappe.get_doc("Sales Invoice", make_invoice(self.card.name))
		self.assertEqual(invoice.net_total, 70)
		invoice.submit()
		self.assertEqual(get_costs(self.card)["external_service_revenue"], 30)
		self.assertIsNone(get_costs(self.card)["gross_margin"])

	def test_return_cannot_repeat_after_full_allocation(self):
		source = self.issue()
		self.move("Consume", source, 6)
		returned = self.move("Return", source, 4, "full-return")
		self.assertEqual(self.move("Return", source, 4, "full-return"), returned)
		with self.assertRaises(frappe.ValidationError):
			self.move("Return", source, 4)

	def test_stock_entry_hook_rejects_warehouse_mismatch(self):
		source = self.issue()
		entry = frappe.get_doc(
			dict(
				doctype="Stock Entry",
				stock_entry_type="Material Issue",
				company=self.company.name,
				service_job_card=self.card.name,
				service_parts_operation="Consume",
				service_posting_request="warehouse-mismatch",
				items=[
					dict(
						item_code=self.item.name,
						qty=1,
						s_warehouse=self.stores,
						service_issue_entry=source.name,
						service_issue_detail=source.items[0].name,
						expense_account=self.expense,
						cost_center=self.cost_center,
					)
				],
			)
		).insert()
		with self.assertRaises(frappe.ValidationError):
			entry.submit()

	def test_partial_billing_reserves_drafts(self):
		source = self.issue()
		self.move("Consume", source, 6)
		frappe.db.set_value("Service Job Card", self.card.name, "internal_maintenance", 0)
		frappe.get_doc("Quotation", make_quotation(self.card.name)).submit()
		first = frappe.get_doc("Sales Invoice", make_invoice(self.card.name))
		first.items[0].qty = 2
		first.save()
		second = frappe.get_doc("Sales Invoice", make_invoice(self.card.name))
		self.assertEqual(second.items[0].qty, 4)
		with self.assertRaises(frappe.ValidationError):
			make_invoice(self.card.name)
		first.submit()
		second.submit()
		self.assertEqual(get_costs(self.card)["parts_revenue"], 120)

	def test_customer_supplied_parts_never_issue_owned_stock(self):
		self.card.parts[0].customer_supplied = 1
		self.card.parts[0].is_billable = 0
		self.card.save()
		with self.assertRaises(frappe.ValidationError):
			self.issue()
		self.assertFalse(allocations(self.card))

	def test_labour_rate_correction_recalculates_once(self):
		employee = frappe.get_doc(
			dict(
				doctype="Employee",
				first_name="Phase2 " + self.token,
				national_identity=self.token,
				gender="Male",
				date_of_birth="1990-01-01",
				date_of_joining="2026-01-01",
				company=self.company.name,
				status="Active",
			)
		).insert()
		self.card.append(
			"labour_entries",
			dict(
				technician=employee.name,
				started_at="2026-11-01 09:00:00",
				stopped_at="2026-11-01 11:00:00",
				internal_cost_rate=25,
				customer_charge_rate=40,
			),
		)
		self.card.save()
		self.card.save()
		self.assertEqual(get_costs(self.card)["actual_labour_cost"], 50)
		self.card.labour_entries[0].internal_cost_rate = 30
		self.card.save()
		self.assertEqual(get_costs(self.card)["actual_labour_cost"], 60)

	def test_historical_stock_reference_reconciliation_preserves_ledgers(self):
		from servicems.legacy_parts import reconcile_historical_parts

		source = self.issue()
		consume = frappe.get_doc("Stock Entry", self.move("Consume", source, 4))
		returned = frappe.get_doc("Stock Entry", self.move("Return", source, 2))
		before = frappe.db.sql(
			"select voucher_no, actual_qty, stock_value_difference from `tabStock Ledger Entry` where company=%s order by name",
			self.company.name,
		)
		for doc in (consume, returned):
			frappe.db.set_value(
				"Stock Entry Detail",
				doc.items[0].name,
				{"service_issue_entry": None, "service_issue_detail": None},
			)
		with self.assertRaises(frappe.ValidationError):
			allocations(self.card)
		result = reconcile_historical_parts(
			self.card.name,
			[
				dict(
					doctype="Stock Entry",
					document=doc.name,
					detail=doc.items[0].name,
					issue_detail=source.items[0].name,
				)
				for doc in (consume, returned)
			],
			"Verified original workshop issue slips",
		)
		self.assertEqual(result[source.items[0].name]["outstanding"], 4)
		self.assertEqual(
			before,
			frappe.db.sql(
				"select voucher_no, actual_qty, stock_value_difference from `tabStock Ledger Entry` where company=%s order by name",
				self.company.name,
			),
		)
		self.assertTrue(
			frappe.db.exists(
				"Comment", {"reference_doctype": "Service Job Card", "reference_name": self.card.name}
			)
		)

	def test_historical_stock_invoice_is_not_consumed_twice(self):
		from servicems.billing import set_item_taxes
		from servicems.legacy_parts import reconcile_historical_parts

		source = self.issue()
		# Reproduce the predecessor's standard stock-updating invoice, with all
		# ERPNext stock, valuation and GL controllers running normally.
		invoice = frappe.get_doc(
			dict(
				doctype="Sales Invoice",
				company=self.company.name,
				customer=self.customer.name,
				service_job_card=self.card.name,
				posting_date=frappe.utils.nowdate(),
				update_stock=1,
				items=[
					dict(
						item_code=self.item.name,
						qty=6,
						rate=20,
						warehouse=self.workshop_wh,
						cost_center=self.cost_center,
					)
				],
			)
		)
		invoice.set_taxes()
		invoice.set_missing_values()
		set_item_taxes(invoice)
		with patch("servicems.billing.validate_invoice"):
			invoice.insert()
			invoice.submit()
		with self.assertRaises(frappe.ValidationError):
			allocations(self.card)
		before = frappe.db.count("Stock Ledger Entry", {"company": self.company.name})
		result = reconcile_historical_parts(
			self.card.name,
			[
				dict(
					doctype="Sales Invoice",
					document=invoice.name,
					detail=invoice.items[0].name,
					issue_detail=source.items[0].name,
				)
			],
			"Verified historical invoice stock ledger",
		)
		self.assertEqual(result[source.items[0].name]["consumed"], 6)
		self.assertEqual(get_costs(self.card)["actual_parts_cost"], 60)
		self.assertEqual(frappe.db.count("Stock Ledger Entry", {"company": self.company.name}), before)
		self.move("Return", source, 4)
		self.assertEqual(allocations(self.card)[source.items[0].name]["outstanding"], 0)
		with self.assertRaises(frappe.ValidationError):
			self.move("Consume", source, 1)

	def test_real_warehouse_company_mismatch_is_rejected(self):
		company = frappe.get_doc(
			dict(
				doctype="Company",
				company_name="P2 Foreign " + self.token,
				abbr="F" + self.token,
				default_currency="TZS",
				country="Tanzania",
			)
		).insert()
		warehouse = frappe.get_doc(
			dict(doctype="Warehouse", warehouse_name="P2 Foreign " + self.token, company=company.name)
		).insert()
		self.workshop.workshop_warehouse = warehouse.name
		self.workshop.save()
		with self.assertRaisesRegex(frappe.ValidationError, "must belong to transaction company"):
			self.issue()
		self.assertEqual(frappe.db.count("Stock Entry", {"service_job_card": self.card.name}), 0)

	def test_post_service_with_multiple_uploaded_photographs(self):
		for task in self.card.tasks:
			task.completed = 1
		self.card.save()
		from frappe.utils.file_manager import save_file

		template = frappe.get_doc(
			dict(
				doctype="Service Pre Inspection Template",
				template_name="P2 Post " + self.token,
				pre_inspection_items=[
					dict(inspection_item="Final result", inspection_type="Data", require_photo=1)
				],
			)
		).insert()
		inspection = frappe.get_doc(
			dict(
				doctype="Service Vehicle Inspection",
				service_job_card=self.card.name,
				inspection_stage="Post-Service",
				inspection_status="Draft",
				inspection_template=template.name,
			)
		).insert()
		photos = []
		for index in range(2):
			content = (
				base64.b64decode(
					"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a7WQAAAAASUVORK5CYII="
				)
				+ b"\n" * index
			)
			photo = save_file(
				f"p2-post-{self.token}-{index}.png",
				content,
				"Service Vehicle Inspection",
				inspection.name,
				is_private=1,
			)
			self.addCleanup(Path(photo.get_full_path()).unlink, missing_ok=True)
			photos.append(photo)
		self.assertNotEqual(photos[0].file_url, photos[1].file_url)
		inspection.image_upload = photos[0].file_url
		inspection.checklist[0].photograph = photos[1].file_url
		inspection.checklist[0].answer = "Repaired"
		inspection.inspection_status = "Completed"
		inspection.save()
		self.assertEqual(inspection.inspection_stage, "Post-Service")
		self.assertEqual(
			frappe.db.count(
				"File", {"attached_to_doctype": inspection.doctype, "attached_to_name": inspection.name}
			),
			2,
		)
