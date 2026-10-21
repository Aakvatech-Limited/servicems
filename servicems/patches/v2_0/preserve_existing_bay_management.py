"""Preserve allocations on upgraded sites without turning Bays on for fresh installs."""

import frappe


def execute():
	# This runs before model sync: the setting's DocField may not exist yet.
	# A stored zero is an explicit customer choice, not a missing setting.
	if "enable_bay_management" in frappe.db.get_singles_dict("Service Settings"):
		return
	for doctype in ("Service Booking", "Service Job Card"):
		if (
			frappe.db.exists("DocType", doctype)
			and frappe.db.has_column(doctype, "bay")
			and frappe.db.count(doctype, {"bay": ["is", "set"]})
		):
			frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
			return
