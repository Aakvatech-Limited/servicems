"""Preserve allocations on upgraded sites without turning Bays on for fresh installs."""

import frappe


def execute():
	if not frappe.db.has_column("tabSingles", "value"):
		return
	if frappe.db.get_single_value("Service Settings", "enable_bay_management"):
		return
	for doctype in ("Service Booking", "Service Job Card"):
		if frappe.db.exists("DocType", doctype) and frappe.db.count(doctype, {"bay": ["is", "set"]}):
			frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
			return
