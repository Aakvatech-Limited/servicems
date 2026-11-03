"""Standard ERPNext quotations and non-stock invoices; no parallel receivables."""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from servicems.costing import charge_lines, get_source_part
from servicems.parts import allocations, copy_dimensions, lock_card


def billed_quantities(card, exclude=None, customer=None, include_drafts=True):
	conditions = " and s.customer=%(customer)s" if customer else ""
	if not include_drafts:
		conditions += " and s.docstatus=1"
	rows = frappe.db.sql(
		"""select d.service_billing_key as billing_key, sum(d.qty) as qty
	 from `tabSales Invoice Item` d join `tabSales Invoice` s on s.name=d.parent
	 where s.service_job_card=%(card)s and s.docstatus!=2 and s.name!=%(exclude)s"""
		+ conditions
		+ " group by d.service_billing_key for update",
		{"card": card.name, "exclude": exclude or "", "customer": customer},
		as_dict=True,
	)
	if any(not row.billing_key for row in rows):
		frappe.throw(_("Reconcile historical invoices before creating further Job Card billing."))
	return {row.billing_key: flt(row.qty) for row in rows}


def payer_share(card, customer, lines):
	if not card.payer_allocations:
		if customer != card.customer:
			frappe.throw(_("Add a payer allocation before billing a different Customer."))
		return 1
	approved = sum(flt(line["qty"]) * flt(line["rate"]) for line in lines)
	allocated = sum(flt(r.approved_amount) for r in card.payer_allocations)
	if any(flt(r.approved_amount) < 0 for r in card.payer_allocations) or abs(allocated - approved) > 0.005:
		frappe.throw(_("Payer allocations must reconcile to the approved billable net amount."))
	amount = sum(flt(r.approved_amount) for r in card.payer_allocations if r.customer == customer)
	if not amount or not approved:
		frappe.throw(_("Selected Customer has no approved payer allocation."))
	return amount / approved


@frappe.whitelist()
def make_invoice(job_card, customer=None):
	card = lock_card(job_card)
	if card.internal_maintenance:
		frappe.throw(_("Internal maintenance does not require a customer invoice."))
	customer = customer or card.customer
	lines = charge_lines(card)
	validate_approval(card, lines)
	share = payer_share(card, customer, lines)
	used = billed_quantities(card, customer=customer)
	doc = frappe.new_doc("Sales Invoice")
	doc.update(
		dict(
			company=card.company,
			customer=customer,
			service_job_card=card.name,
			posting_date=nowdate(),
			due_date=nowdate(),
			update_stock=0,
			currency=frappe.get_cached_value("Company", card.company, "default_currency"),
		)
	)
	copy_dimensions(card, doc)
	for line in lines:
		qty = flt(line["qty"] - used.get(line["key"], 0), 6)
		if qty > 0:
			row = doc.append(
				"items",
				dict(
					item_code=line["item_code"],
					qty=qty,
					rate=flt(line["rate"] * share, 6),
					service_billing_key=line["key"],
					warehouse=frappe.get_cached_value(
						"Service Workshop", card.workshop, "workshop_warehouse"
					),
					cost_center=card.cost_center,
				),
			)
			copy_dimensions(card, row)
	if not doc.items:
		frappe.throw(_("No unbilled approved charges remain for this payer."))
	doc.set_taxes()
	doc.set_missing_values()
	set_item_taxes(doc)
	doc.calculate_taxes_and_totals()
	doc.insert()
	if not card.invoice:
		frappe.db.set_value("Service Job Card", card.name, "invoice", doc.name, update_modified=False)
	return doc.name


def validate_invoice(doc, method=None):
	if not doc.get("service_job_card"):
		return
	card = lock_card(doc.service_job_card)
	validate_discounts(doc)
	if doc.company != card.company or doc.currency != frappe.get_cached_value(
		"Company", card.company, "default_currency"
	):
		frappe.throw(_("Job Card invoices must use its company and company currency."))
	if doc.update_stock:
		frappe.throw(
			_("Post Job Card consumption through Material Issue before billing; disable Update Stock.")
		)
	lines = charge_lines(card)
	validate_approval(card, lines)
	share = payer_share(card, doc.customer, lines)
	allowed = {r["key"]: r for r in lines}
	used = billed_quantities(card, exclude=doc.name, customer=doc.customer)
	requested = {}
	for row in doc.items:
		line = allowed.get(row.service_billing_key)
		if (
			not line
			or row.item_code != line["item_code"]
			or abs(flt(row.rate) - flt(line["rate"] * share, 6)) > 0.005
		):
			frappe.throw(_("Invoice rows must match approved Job Card billing references and rates."))
		if not doc.is_return and row.qty <= 0:
			frappe.throw(_("Invoice quantities must be positive."))
		requested[row.service_billing_key] = requested.get(row.service_billing_key, 0) + flt(row.qty)
	for key, qty in requested.items():
		total = flt(used.get(key, 0) + qty, 6)
		if total < -0.000001 or total > allowed[key]["qty"] + 0.000001:
			frappe.throw(_("Invoice quantity exceeds the payer's unbilled allocation."))


@frappe.whitelist()
def make_quotation(job_card):
	card = lock_card(job_card)
	if card.internal_maintenance:
		frappe.throw(_("Internal maintenance does not require a quotation."))
	doc = frappe.new_doc("Quotation")
	doc.update(
		dict(
			company=card.company,
			quotation_to="Customer",
			party_name=card.customer,
			order_type="Sales",
			service_job_card=card.name,
		)
	)
	# Estimates include planned parts before consumption; billing uses actual consumption.
	lines = [
		dict(
			key=("external:" if r.charge_category == "External Service" else "service:") + r.name,
			item_code=r.item,
			qty=1,
			rate=r.rate,
		)
		for r in card.services
		if r.is_billable
	]
	lines += [
		dict(key="estimate:" + r.name, item_code=r.item, qty=r.qty, rate=r.rate)
		for r in card.parts
		if r.is_billable and not r.customer_supplied
	]
	lines += [
		dict(key="labour:" + r.name, item_code=card.labour_item, qty=r.hours, rate=r.customer_charge_rate)
		for r in card.labour_entries
		if r.is_billable and r.hours
	]
	for detail, bucket in allocations(card).items():
		if not bucket["row"].service_part_row:
			part = get_source_part(card, bucket["row"])
			if part and part.is_billable:
				lines.append(
					dict(
						key="legacy:" + detail,
						item_code=part.item,
						qty=bucket["issued"] - bucket["returned"],
						rate=part.rate,
					)
				)
	covered = frappe.db.sql(
		"""select d.service_billing_key as billing_key, q.name from `tabQuotation Item` d join `tabQuotation` q on q.name=d.parent where q.service_job_card=%s and q.docstatus!=2 for update""",
		card.name,
		as_dict=True,
	)
	covered_keys = {r.billing_key for r in covered}
	lines = [line for line in lines if line["key"] not in covered_keys]
	if not lines and covered:
		return covered[-1].name
	for line in lines:
		doc.append(
			"items",
			dict(
				item_code=line["item_code"],
				qty=line["qty"],
				rate=line["rate"],
				service_billing_key=line["key"],
			),
		)
	if not doc.items:
		frappe.throw(_("Add billable services or planned parts before creating an estimate."))
	doc.set_taxes()
	doc.set_missing_values()
	set_item_taxes(doc)
	doc.calculate_taxes_and_totals()
	doc.insert()
	if not card.quotation:
		frappe.db.set_value("Service Job Card", card.name, "quotation", doc.name, update_modified=False)
	return doc.name


def validate_supplier_invoice(doc, method=None):
	for row in doc.items:
		if not row.get("service_job_card"):
			continue
		card = lock_card(row.service_job_card)
		if not card.cost_center:
			frappe.throw(_("Set the Job Card cost center before recording an external repair expense."))
		if doc.company != card.company or (row.cost_center and row.cost_center != card.cost_center):
			frappe.throw(_("External repair company and cost center must match the Job Card."))
		if frappe.get_cached_value("Item", row.item_code, "is_stock_item"):
			frappe.throw(
				_("Link external non-stock repair services to the Job Card; use Material Issue for parts.")
			)
		if (
			row.expense_account
			and frappe.get_cached_value("Account", row.expense_account, "root_type") != "Expense"
		):
			frappe.throw(_("External repairs must use an expense account."))
		row.cost_center = card.cost_center
		copy_dimensions(card, row)


def validate_approval(card, lines):
	"""Submitted ERPNext quotations are the approval and revision record."""
	approved = frappe.db.sql(
		"""select d.service_billing_key as billing_key, d.item_code, d.rate, sum(d.qty) as qty
	 from `tabQuotation Item` d join `tabQuotation` q on q.name=d.parent
	 where q.service_job_card=%s and q.docstatus=1
	 group by d.service_billing_key, d.item_code, d.rate for update""",
		card.name,
		as_dict=True,
	)
	by_key = {row.billing_key: row for row in approved}
	for line in lines:
		key = line["key"]
		if key.startswith("parts:"):
			detail = frappe.db.get_value("Stock Entry Detail", key.split(":", 1)[1], "service_part_row")
			key = "estimate:" + detail if detail else "legacy:" + key.split(":", 1)[1]
		row = by_key.get(key)
		if (
			not row
			or row.item_code != line["item_code"]
			or abs(flt(row.rate) - line["rate"]) > 0.005
			or line["qty"] > flt(row.qty) + 0.000001
		):
			frappe.throw(
				_(
					"Submit an approved repair quotation covering all billable quantities and rates before invoicing."
				)
			)


def validate_quotation(doc, method=None):
	if not doc.get("service_job_card"):
		return
	card = lock_card(doc.service_job_card)
	validate_discounts(doc)
	if doc.company != card.company or doc.party_name != card.customer:
		frappe.throw(_("Repair quotations must match the Job Card company and vehicle owner Customer."))
	seen = set()
	for row in doc.items:
		if not row.service_billing_key or row.service_billing_key in seen:
			frappe.throw(_("Each quotation row requires a unique Job Card billing reference."))
		seen.add(row.service_billing_key)
		if frappe.db.sql(
			"""select d.name from `tabQuotation Item` d join `tabQuotation` q on q.name=d.parent where q.service_job_card=%s and q.docstatus!=2 and q.name!=%s and d.service_billing_key=%s for update""",
			(card.name, doc.name, row.service_billing_key),
		):
			frappe.throw(
				_(
					"This repair is already covered by an active quotation. Cancel and amend it for a revision."
				)
			)


def set_item_taxes(doc):
	from erpnext.stock.get_item_details import ItemDetailsCtx, get_item_tax_map, get_item_tax_template

	for row in doc.items:
		ctx = ItemDetailsCtx(
			{
				"item_code": row.item_code,
				"company": doc.company,
				"posting_date": doc.get("posting_date") or doc.get("transaction_date"),
				"transaction_date": doc.get("transaction_date") or doc.get("posting_date"),
				"tax_category": doc.get("tax_category"),
				"base_net_rate": flt(row.rate) * flt(doc.conversion_rate or 1),
				"child_doctype": row.doctype,
			}
		)
		row.item_tax_template = get_item_tax_template(ctx, item=frappe.get_doc("Item", row.item_code))
		row.item_tax_rate = get_item_tax_map(doc=doc, tax_template=row.item_tax_template)


def validate_closure(card):
	lines = charge_lines(card)
	if not lines:
		return
	validate_approval(card, lines)
	customers = {r.customer for r in card.payer_allocations if flt(r.approved_amount) > 0} or {card.customer}
	for customer in customers:
		payer_share(card, customer, lines)
		quantities = billed_quantities(card, customer=customer, include_drafts=False)
		if any(quantities.get(line["key"], 0) < line["qty"] - 0.000001 for line in lines):
			frappe.throw(
				_("Submit invoices for all approved payer charges before closing a commercial Job Card.")
			)


def validate_discounts(doc):
	if (
		doc.get("discount_amount")
		or doc.get("additional_discount_percentage")
		or any(row.get("discount_amount") or row.get("discount_percentage") for row in doc.items)
	):
		frappe.throw(
			_(
				"Revise and approve Job Card quotation rates before applying a discount; invoice charges must match the approved rates."
			)
		)
