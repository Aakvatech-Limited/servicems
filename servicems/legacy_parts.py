"""Opt-in metadata reconciliation for historical standard ERPNext movements."""

import html

import frappe
from frappe import _

from servicems.parts import allocations, lock_card, movements


@frappe.whitelist()
def reconcile_historical_parts(job_card, mappings, reason):
	"""Add exact source-row references with an audit comment; never change ledgers."""
	frappe.only_for("System Manager")
	if not reason or not reason.strip():
		frappe.throw(_("Provide the reason and supporting reconciliation reference."))
	card = lock_card(job_card)
	workshop = frappe.get_doc("Service Workshop", card.workshop)
	rows = movements(card)
	sources = {
		row.name: row
		for row in rows
		if row.purpose == "Material Transfer"
		and row.s_warehouse == workshop.parts_warehouse
		and row.t_warehouse == workshop.workshop_warehouse
		and not row.is_return
	}
	mappings = frappe.parse_json(mappings)
	if not isinstance(mappings, list) or not mappings:
		frappe.throw(_("Supply an explicit mapping for each historical movement item."))
	frappe.db.savepoint("service_legacy_mapping")
	try:
		for mapping in mappings:
			doctype = mapping.get("doctype")
			if doctype not in ("Stock Entry", "Sales Invoice"):
				frappe.throw(
					_("Only standard stock movements and stock-updating invoices can be reconciled.")
				)
			doc = frappe.get_doc(doctype, mapping.get("document"), for_update=True)
			doc.check_permission("write")
			if doc.docstatus != 1 or doc.service_job_card != card.name or doc.company != card.company:
				frappe.throw(_("Historical movement must be submitted for the same Job Card and company."))
			row = next((r for r in doc.items if r.name == mapping.get("detail")), None)
			source = sources.get(mapping.get("issue_detail"))
			if not row or not source or row.item_code != source.item_code:
				frappe.throw(_("Select the exact historical movement and source issue item rows."))
			if doctype == "Stock Entry":
				if row.s_warehouse != workshop.workshop_warehouse or (
					doc.purpose != "Material Issue"
					and not (
						doc.purpose == "Material Transfer" and row.t_warehouse == workshop.parts_warehouse
					)
				):
					frappe.throw(
						_(
							"Historical movement must be actual workshop consumption or a return to parts stores."
						)
					)
			elif not doc.update_stock or row.warehouse != workshop.workshop_warehouse:
				frappe.throw(_("Historical invoice must have consumed stock from this workshop."))
			if row.service_issue_detail and row.service_issue_detail != source.name:
				frappe.throw(
					_(
						"Existing source references cannot be overwritten; reverse and amend the standard document for corrections."
					)
				)
			values = {"service_issue_entry": source.stock_entry, "service_issue_detail": source.name}
			if doctype == "Sales Invoice":
				if row.service_billing_key and row.service_billing_key != "parts:" + source.name:
					frappe.throw(_("Existing invoice billing references cannot be overwritten."))
				values["service_billing_key"] = "parts:" + source.name
			frappe.db.set_value(row.doctype, row.name, values, update_modified=False)
		result = allocations(card)
		card.add_comment(
			"Comment",
			"Historical parts reconciliation: "
			+ html.escape(reason)
			+ "<pre>"
			+ html.escape(frappe.as_json(mappings))
			+ "</pre>",
		)
		return result
	except Exception:
		frappe.db.rollback(save_point="service_legacy_mapping")
		raise
