"""Keep Bay Management enabled on installations already using workshop records."""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Service Settings"):
		return
	if any(frappe.db.exists(doctype) for doctype in ("Bay", "Service Booking", "Service Job Card")):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
