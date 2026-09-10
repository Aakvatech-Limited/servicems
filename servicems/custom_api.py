import frappe
from erpnext.stock.doctype.batch.batch import get_batch_qty
from frappe.utils import cint, flt, getdate, nowdate


@frappe.whitelist()
def get_item_info(item_code: str):
	"""Available stock per warehouse, split by batch for batched items, with batch expiry."""
	precision = cint(frappe.db.get_default("float_precision")) or 3
	item = frappe.db.get_value("Item", item_code, ["stock_uom", "has_batch_no"], as_dict=True)
	if not item:
		return []

	bins = frappe.get_all(
		"Bin",
		filters={"item_code": item_code, "actual_qty": ["!=", 0]},
		fields=["warehouse", "actual_qty"],
		order_by="warehouse",
	)

	results = []
	for bin_row in bins:
		if item.has_batch_no:
			rows = get_batch_rows(item_code, bin_row.warehouse)
		else:
			rows = [{"batch_no": None, "qty": bin_row.actual_qty}]

		for row in rows:
			expires_on, expiry_status = get_expiry(row["batch_no"])
			results.append(
				{
					"item_code": item_code,
					"warehouse": bin_row.warehouse,
					"batch_no": row["batch_no"],
					"actual_qty": flt(row["qty"], precision),
					"expires_on": expires_on,
					"expiry_status": expiry_status,
					"stock_uom": item.stock_uom,
				}
			)

	return results


def get_batch_rows(item_code: str, warehouse: str):
	"""Batch balances come from the Serial and Batch Bundle ledger in ERPNext v15+."""
	batches = get_batch_qty(item_code=item_code, warehouse=warehouse, for_stock_levels=True)
	return [
		{"batch_no": batch.get("batch_no"), "qty": batch.get("qty")} for batch in batches if batch.get("qty")
	]


def get_expiry(batch_no: str | None):
	expiry_date = frappe.db.get_value("Batch", batch_no, "expiry_date") if batch_no else None
	if not expiry_date:
		return None, None

	expiry_date = getdate(expiry_date)
	days_to_expire = (expiry_date - getdate(nowdate())).days
	return expiry_date, max(days_to_expire, 0)
