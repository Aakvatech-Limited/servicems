"""Actual costs and commercial charges derived from standard linked documents."""

import frappe
from frappe import _
from frappe.utils import flt


def charge_lines(card):
	from servicems.parts import allocations

	lines = []
	for row in card.services:
		if row.is_billable:
			lines.append(
				dict(
					key=("external:" if row.charge_category == "External Service" else "service:") + row.name,
					category="external" if row.charge_category == "External Service" else "labour",
					item_code=row.item,
					qty=1,
					rate=flt(row.rate),
				)
			)
	if card.labour_item and frappe.get_cached_value("Item", card.labour_item, "is_stock_item"):
		frappe.throw(_("Labour Billing Item must be a non-stock item."))
	for row in card.labour_entries:
		if row.is_billable and row.hours:
			if not card.labour_item:
				frappe.throw(_("Set a Labour Billing Item for billable time entries."))
			lines.append(
				dict(
					key="labour:" + row.name,
					category="labour",
					item_code=card.labour_item,
					qty=flt(row.hours),
					rate=flt(row.customer_charge_rate),
				)
			)
	for detail, bucket in allocations(card).items():
		if not bucket["consumed"]:
			continue
		source = bucket["row"]
		part = get_source_part(card, source)
		if part and part.is_billable:
			lines.append(
				dict(
					key="parts:" + detail,
					category="parts",
					item_code=source.item_code,
					qty=bucket["consumed"],
					rate=flt(part.rate),
				)
			)
	return lines


def get_costs(card):
	result = dict(
		actual_labour_hours=0,
		actual_labour_cost=0,
		actual_parts_cost=0,
		external_service_cost=0,
		parts_revenue=0,
		labour_revenue=0,
		external_service_revenue=0,
	)
	for row in card.labour_entries:
		result["actual_labour_hours"] += flt(row.hours)
		result["actual_labour_cost"] += flt(row.hours) * flt(row.internal_cost_rate)
	result["actual_parts_cost"] = flt(
		frappe.db.sql(
			"""select -sum(l.stock_value_difference) from `tabStock Ledger Entry` l join `tabStock Entry` s on s.name=l.voucher_no where l.voucher_type='Stock Entry' and l.is_cancelled=0 and s.service_job_card=%s and s.purpose='Material Issue' and s.docstatus=1""",
			card.name,
		)[0][0]
	)
	result["actual_parts_cost"] += flt(
		frappe.db.sql(
			"""select -sum(l.stock_value_difference) from `tabStock Ledger Entry` l join `tabSales Invoice` s on s.name=l.voucher_no where l.voucher_type='Sales Invoice' and l.is_cancelled=0 and s.service_job_card=%s and s.update_stock=1 and s.docstatus=1""",
			card.name,
		)[0][0]
	)
	result["external_service_cost"] = flt(
		frappe.db.sql(
			"""select sum(d.base_net_amount) from `tabPurchase Invoice Item` d join `tabPurchase Invoice` p on p.name=d.parent where d.service_job_card=%s and p.docstatus=1""",
			card.name,
		)[0][0]
	)
	rows = frappe.db.sql(
		"""select d.service_billing_key, d.base_net_amount from `tabSales Invoice Item` d join `tabSales Invoice` s on s.name=d.parent where s.service_job_card=%s and s.docstatus=1""",
		card.name,
		as_dict=True,
	)
	for row in rows:
		category = (
			"parts"
			if (row.service_billing_key or "").startswith("parts:")
			else ("external_service" if (row.service_billing_key or "").startswith("external:") else "labour")
		)
		result[category + "_revenue"] += flt(row.base_net_amount)
	result["total_actual_cost"] = (
		result["actual_labour_cost"] + result["actual_parts_cost"] + result["external_service_cost"]
	)
	result["cost_variance"] = result["total_actual_cost"] - flt(card.estimated_cost)
	result["gross_margin"] = (
		None
		if not card.costs_confirmed
		else sum(result[k] for k in ("parts_revenue", "labour_revenue", "external_service_revenue"))
		- result["total_actual_cost"]
	)
	return result


def validate_costing(card):
	previous = card.get_doc_before_save()
	if previous and frappe.db.exists(
		"Sales Invoice", {"service_job_card": card.name, "docstatus": ["!=", 2]}
	):
		old = [(r.customer, r.responsibility, flt(r.approved_amount)) for r in previous.payer_allocations]
		new = [(r.customer, r.responsibility, flt(r.approved_amount)) for r in card.payer_allocations]
		if old != new or previous.internal_maintenance != card.internal_maintenance:
			frappe.throw(
				_(
					"Reverse existing invoices before changing payer allocations or internal maintenance treatment."
				)
			)
	for row in card.parts:
		if row.customer_supplied and row.is_billable:
			frappe.throw(
				_(
					"Customer-supplied parts cannot be billed as owned stock. Add installation charges as a service."
				)
			)
	for row in card.labour_entries:
		if min(flt(row.internal_cost_rate), flt(row.customer_charge_rate)) < 0:
			frappe.throw(_("Labour rates cannot be negative."))
		row.actual_cost = flt(row.hours) * flt(row.internal_cost_rate)
		row.charge_amount = flt(row.hours) * flt(row.customer_charge_rate) if row.is_billable else 0
	for dt, field in (("Account", "expense_account"), ("Cost Center", "cost_center")):
		if card.get(field) and frappe.get_cached_value(dt, card.get(field), "company") != card.company:
			frappe.throw(_("Costing account and cost center must belong to the Job Card company."))
	if card.expense_account:
		account = frappe.get_cached_doc("Account", card.expense_account)
		if account.is_group or account.root_type != "Expense":
			frappe.throw(_("Maintenance Expense Account must be a ledger expense account."))
	if not card.is_new():
		card.update(get_costs(card))


@frappe.whitelist()
def get_job_costs(job_card):
	card = frappe.get_doc("Service Job Card", job_card)
	card.check_permission("read")
	return get_costs(card)


def get_source_part(card, source):
	part = next((r for r in card.parts if r.name == source.service_part_row), None)
	if part:
		return part
	candidates = [
		r for r in card.supplied_parts if r.stock_entry == source.stock_entry and r.item == source.item_code
	]
	if len({(flt(r.rate), r.is_billable) for r in candidates}) > 1:
		frappe.throw(
			_(
				"Historical supplied part rates are ambiguous; reconcile the source documents before further billing."
			)
		)
	return candidates[0] if candidates else None
