from datetime import date

import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import IfNull, Max
from frappe.utils import cint, flt, getdate


@frappe.whitelist()
def get_item_info(item_code):
	"""
	Get available stock by batch and warehouse for the given item.
	Includes expiry info and quantity from latest stock ledger entries.
	"""
	float_precision = cint(frappe.db.get_default("float_precision")) or 3

	stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")

	# Inline stock ledger query (latest entries per warehouse + batch)
	stock_ledger = DocType("Stock Ledger Entry")
	sle_max = (
		frappe.qb.from_(stock_ledger)
		.select(
			IfNull(stock_ledger.batch_no, "").as_("batch_no"),
			stock_ledger.item_code,
			stock_ledger.warehouse,
			Max(stock_ledger.posting_datetime).as_("posting_datetime"),
		)
		.where(stock_ledger.docstatus == 1)
		.groupby(IfNull(stock_ledger.batch_no, ""), stock_ledger.item_code, stock_ledger.warehouse)
	).as_("sle_max")

	sle = (
		frappe.qb.from_(stock_ledger)
		.inner_join(sle_max)
		.on(
			(IfNull(stock_ledger.batch_no, "") == sle_max.batch_no)
			& (stock_ledger.item_code == sle_max.item_code)
			& (stock_ledger.warehouse == sle_max.warehouse)
			& (stock_ledger.posting_datetime == sle_max.posting_datetime)
		)
		.select(
			stock_ledger.batch_no,
			stock_ledger.item_code,
			stock_ledger.warehouse,
			stock_ledger.qty_after_transaction.as_("actual_qty"),
		)
		.where((stock_ledger.docstatus == 1) & (stock_ledger.item_code == item_code))
		.orderby(stock_ledger.warehouse, stock_ledger.item_code, stock_ledger.batch_no)
	).run(as_dict=True)

	# Build quantity map
	iwb_map = {}

	for d in sle:
		iwb_map.setdefault(d.item_code, {}).setdefault(d.warehouse, {}).setdefault(
			d.batch_no, frappe._dict({"bal_qty": 0.0})
		)
		qty_dict = iwb_map[d.item_code][d.warehouse][d.batch_no]

		# Fetch expiry date for the batch (if any)
		expiry_date_str = frappe.db.get_value("Batch", d.batch_no, "expiry_date") if d.batch_no else None

		if expiry_date_str:
			expiry_date = getdate(expiry_date_str)
			qty_dict.expires_on = expiry_date
			days_to_expire = (expiry_date - date.today()).days
			qty_dict.expiry_status = days_to_expire if days_to_expire > 0 else 0

		qty_dict.actual_qty = flt(qty_dict.actual_qty, float_precision) + flt(d.actual_qty, float_precision)

	# Format result list
	results = []
	for item_code, warehouses in iwb_map.items():
		for warehouse, batches in warehouses.items():
			for batch_no, info in batches.items():
				result = {
					"item_code": item_code,
					"warehouse": warehouse,
					"batch_no": batch_no,
					"actual_qty": flt(info.actual_qty, float_precision),
					"expires_on": info.get("expires_on"),
					"expiry_status": info.get("expiry_status"),
					"stock_uom": stock_uom,
				}
				results.append(result)

	return results
