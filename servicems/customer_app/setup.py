"""Idempotent setup of the delegated Customer App manager role."""

import frappe

from servicems.customer_app.security import MANAGER_ROLE


def ensure_role():
	if not frappe.db.exists("Role", MANAGER_ROLE):
		frappe.get_doc(
			{"doctype": "Role", "role_name": MANAGER_ROLE, "desk_access": 1}
		).insert(ignore_permissions=True)
