"""Job Card allocations backed exclusively by submitted ERPNext Stock Entries."""

import json
import math

import frappe
from frappe import _
from frappe.utils import flt, nowdate, nowtime

from servicems.service_management.doctype.service_job_card.service_job_card import reconcile_parts_quantities


def lock_card(name, permission="write"):
	card = frappe.get_doc("Service Job Card", name)
	card.check_permission(permission)
	card = frappe.get_doc("Service Job Card", name, for_update=True)
	if card.docstatus == 2:
		frappe.throw(_("Cannot post against a cancelled Job Card."))
	return card


def movements(card):
	return frappe.db.sql(
		"""select d.*, s.purpose, s.service_parts_operation, s.is_return,
		 s.company, s.name as stock_entry from `tabStock Entry Detail` d
		 join `tabStock Entry` s on s.name=d.parent
		 where s.service_job_card=%s and s.docstatus=1 order by s.creation, d.idx for update""",
		card.name,
		as_dict=True,
	)


def allocations(card):
	workshop = frappe.get_doc("Service Workshop", card.workshop)

	rows = movements(card)
	issued = {}
	for row in rows:
		if (
			row.purpose == "Material Transfer"
			and row.s_warehouse == workshop.parts_warehouse
			and row.t_warehouse == workshop.workshop_warehouse
			and not row.is_return
		):
			issued[row.name] = {"row": row, "issued": flt(row.transfer_qty), "consumed": 0, "returned": 0}
	for row in rows:
		if row.name in issued:
			continue
		if not row.service_issue_detail or row.service_issue_detail not in issued:
			# Historical unallocated postings cannot safely be assigned by item alone.
			frappe.throw(
				_(
					"Reconcile historical Stock Entry {0} to its issued item rows before posting further movements."
				).format(row.stock_entry)
			)
		bucket = issued[row.service_issue_detail]
		key = "consumed" if row.purpose == "Material Issue" else "returned"
		bucket[key] += flt(row.transfer_qty)
	legacy_rows = frappe.db.sql(
		"""select d.name, d.item_code, d.warehouse, d.stock_qty, d.service_issue_entry, d.service_issue_detail, s.name as invoice
	 from `tabSales Invoice Item` d join `tabSales Invoice` s on s.name=d.parent join `tabItem` i on i.name=d.item_code
	 where s.service_job_card=%s and s.docstatus=1 and s.update_stock=1 and i.is_stock_item=1 for update""",
		card.name,
		as_dict=True,
	)
	for row in legacy_rows:
		bucket = issued.get(row.service_issue_detail)
		if (
			not bucket
			or bucket["row"].stock_entry != row.service_issue_entry
			or bucket["row"].item_code != row.item_code
			or row.warehouse != workshop.workshop_warehouse
		):
			frappe.throw(
				_(
					"Reconcile historical stock-updating invoice {0} to its source issue item rows before posting further movements."
				).format(row.invoice)
			)
		bucket["consumed"] += flt(row.stock_qty)
	for bucket in issued.values():
		bucket.update(reconcile_parts_quantities(bucket["issued"], bucket["consumed"], bucket["returned"]))
	return issued


def source_row(card, detail):
	bucket = allocations(card).get(detail)
	if not bucket:
		frappe.throw(_("Select a submitted issue item belonging to this Job Card."))
	return bucket


def validate_entry(doc, method=None):
	if not doc.get("service_job_card"):
		return
	card = lock_card(doc.service_job_card)
	workshop = frappe.get_doc("Service Workshop", card.workshop)
	card.validate_stock_transfer_configuration(workshop, card.company)
	if doc.company != card.company:
		frappe.throw(_("Stock Entry company must match the Job Card."))
	if not doc.get("service_posting_request"):
		frappe.throw(
			_("Use the Job Card posting actions to create stock movements with a unique request reference.")
		)
	if frappe.db.sql(
		"""select name from `tabStock Entry` where service_job_card=%s and service_posting_request=%s and name!=%s for update""",
		(card.name, doc.service_posting_request, doc.name),
	):
		frappe.throw(_("This stock posting request has already been used."))
	operation = doc.get("service_parts_operation")
	if operation not in ("Issue", "Consume", "Return"):
		frappe.throw(_("Select a Service Parts Operation for Job Card stock movements."))
	purpose = "Material Issue" if operation == "Consume" else "Material Transfer"
	if doc.purpose != purpose:
		frappe.throw(_("Stock Entry purpose does not match the Service Parts Operation."))
	current = allocations(card)
	requested = {}
	planned = set()
	if operation == "Issue" and (card.docstatus != 0 or card.status in ("Completed", "Closed")):
		frappe.throw(_("Reopen the Job Card before issuing further parts."))
	for row in doc.items:
		qty = flt(row.transfer_qty)
		if not math.isfinite(qty) or qty <= 0:
			frappe.throw(_("Parts quantities must be greater than zero."))
		expected_source = workshop.parts_warehouse if operation == "Issue" else workshop.workshop_warehouse
		expected_target = (
			workshop.workshop_warehouse
			if operation == "Issue"
			else (workshop.parts_warehouse if operation == "Return" else None)
		)
		if row.s_warehouse != expected_source or (row.t_warehouse or None) != expected_target:
			frappe.throw(_("Stock Entry warehouses do not match the workshop operation."))
		if operation == "Issue":
			part = next((p for p in card.parts if p.name == row.service_part_row), None)
			if (
				not part
				or part.item != row.item_code
				or flt(part.qty, 6) != qty
				or part.use_existing_spares
				or part.customer_supplied
			):
				frappe.throw(_("Issue rows must match the planned Job Card item and quantity."))
			if part.name in planned or any(b["row"].service_part_row == part.name for b in current.values()):
				frappe.throw(_("This planned part row has already been issued."))
			planned.add(part.name)
			if row.service_issue_detail or row.service_issue_entry:
				frappe.throw(_("An issue cannot reference another issue."))
			continue
		bucket = current.get(row.service_issue_detail)
		if (
			not bucket
			or bucket["row"].stock_entry != row.service_issue_entry
			or bucket["row"].item_code != row.item_code
		):
			frappe.throw(_("Invalid source issue item reference."))
		requested[row.service_issue_detail] = requested.get(row.service_issue_detail, 0) + qty
		if operation == "Consume":
			if not card.expense_account or not card.cost_center:
				frappe.throw(_("Set the maintenance expense account and cost center on the Job Card."))
			if row.expense_account != card.expense_account or row.cost_center != card.cost_center:
				frappe.throw(_("Consumption accounting must match the Job Card."))
	for detail, qty in requested.items():
		bucket = current[detail]
		reconcile_parts_quantities(
			bucket["issued"],
			bucket["consumed"] + (qty if operation == "Consume" else 0),
			bucket["returned"] + (qty if operation == "Return" else 0),
		)


def validate_cancel(doc, method=None):
	if not doc.get("service_job_card"):
		return
	card = lock_card(doc.service_job_card)
	if frappe.db.exists("Sales Invoice", {"service_job_card": card.name, "docstatus": ["!=", 2]}):
		frappe.throw(_("Cancel or delete linked invoices before reversing Job Card stock movements."))
	if doc.get("service_parts_operation") == "Issue" or (
		doc.purpose == "Material Transfer" and not doc.is_return
	):
		for bucket in allocations(card).values():
			if bucket["row"].stock_entry == doc.name and (bucket["consumed"] or bucket["returned"]):
				frappe.throw(_("Reverse consumption and returns before cancelling the issue."))


def copy_dimensions(card, target):
	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions

	for field in get_accounting_dimensions():
		if card.meta.has_field(field) and target.meta.has_field(field):
			target.set(field, card.get(field))


@frappe.whitelist()
def post_parts(job_card, operation, items, request_id):
	"""Idempotent posting. The Job Card row lock serializes every stock mutation."""
	card = lock_card(job_card)
	if (
		operation not in ("Issue", "Consume", "Return")
		or not isinstance(request_id, str)
		or not request_id
		or len(request_id) > 140
	):
		frappe.throw(_("Provide a valid operation and unique posting request ID."))
	items = frappe.parse_json(items)
	if not isinstance(items, list) or not items:
		frappe.throw(_("Select at least one item."))
	fingerprint = json.dumps({"operation": operation, "items": items}, sort_keys=True)
	prior = frappe.db.sql(
		"""select name, service_request_payload, docstatus from `tabStock Entry` where service_job_card=%s and service_posting_request=%s for update""",
		(card.name, request_id),
		as_dict=True,
	)
	previous = prior[0] if prior else None
	if previous:
		if previous.service_request_payload != fingerprint or previous.docstatus != 1:
			frappe.throw(
				_(
					"Posting request was already used. Use a new request for a corrected or reversed transaction."
				)
			)
		return previous.name
	workshop = frappe.get_doc("Service Workshop", card.workshop)
	card.validate_stock_transfer_configuration(workshop, card.company)
	doc = frappe.new_doc("Stock Entry")
	doc.update(
		{
			"company": card.company,
			"stock_entry_type": "Material Issue" if operation == "Consume" else "Material Transfer",
			"purpose": "Material Issue" if operation == "Consume" else "Material Transfer",
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"service_job_card": card.name,
			"service_parts_operation": operation,
			"service_posting_request": request_id,
			"service_request_payload": fingerprint,
		}
	)
	copy_dimensions(card, doc)
	for item in items:
		qty = flt(item.get("qty"), 6)
		if not math.isfinite(qty) or qty <= 0:
			frappe.throw(_("Parts quantities must be greater than zero."))
		if operation == "Issue":
			part = next((r for r in card.parts if r.name == item.get("part_row")), None)
			if not part or part.use_existing_spares or part.customer_supplied or qty != flt(part.qty, 6):
				frappe.throw(_("Select an unissued Job Card part row with its full planned quantity."))
			# Existing submitted or cancelled requests retain their plan row reference.
			if frappe.db.sql(
				"""select d.name from `tabStock Entry Detail` d join `tabStock Entry` s on s.name=d.parent where s.service_job_card=%s and s.docstatus=1 and d.service_part_row=%s""",
				(card.name, part.name),
			):
				frappe.throw(_("This Job Card part row has already been issued."))
			values = {
				"item_code": part.item,
				"service_part_row": part.name,
				"s_warehouse": workshop.parts_warehouse,
				"t_warehouse": workshop.workshop_warehouse,
			}
		else:
			bucket = source_row(card, item.get("issue_detail"))
			source = bucket["row"]
			values = {
				"item_code": source.item_code,
				"service_issue_detail": source.name,
				"service_issue_entry": source.stock_entry,
				"s_warehouse": workshop.workshop_warehouse,
				"t_warehouse": workshop.parts_warehouse if operation == "Return" else None,
			}
			if operation == "Consume":
				values.update(expense_account=card.expense_account, cost_center=card.cost_center)
		row = doc.append(
			"items",
			{
				**values,
				"qty": qty,
				"uom": frappe.get_cached_value("Item", values["item_code"], "stock_uom"),
				"conversion_factor": 1,
			},
		)
		copy_dimensions(card, row)
	doc.insert()
	doc.submit()
	return doc.name


@frappe.whitelist()
def get_allocations(job_card):
	card = frappe.get_doc("Service Job Card", job_card)
	card.check_permission("read")
	return allocations(card)
