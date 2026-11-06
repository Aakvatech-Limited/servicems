"""Central fail-closed, company-scoped guards for the ServiceMS Customer App.

Never replace Frappe's global login or standard ERPNext Portal policies.
"""

import frappe
from frappe import _
from frappe.utils import cint

MANAGER_ROLE = "ServiceMS Customer App Manager"


def _global_admin(user):
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def _managed_companies(user):
	if MANAGER_ROLE not in frappe.get_roles(user):
		return set()
	# Explicit User Permissions are mandatory for delegated company managers.
	permissions = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Company"},
		fields=["for_value", "applicable_for"],
	)
	return {
		row.for_value
		for row in permissions
		if not row.applicable_for
		or row.applicable_for in ("Customer App Settings", "Customer App Account")
	}


def can_manage_company(company, user=None):
	user = user or frappe.session.user
	return bool(company and (_global_admin(user) or company in _managed_companies(user)))


def settings_query_conditions(user=None):
	user = user or frappe.session.user
	if _global_admin(user):
		return ""
	companies = _managed_companies(user)
	if not companies:
		return "1=0"
	values = ", ".join(frappe.db.escape(company) for company in sorted(companies))
	return f"`tabCustomer App Settings`.`company` IN ({values})"


def accounts_query_conditions(user=None):
	return settings_query_conditions(user).replace("tabCustomer App Settings", "tabCustomer App Account")


def settings_has_permission(doc, user=None, permission_type=None):
	return can_manage_company(doc.company, user)


def account_has_permission(doc, user=None, permission_type=None):
	return can_manage_company(doc.company, user)


def enabled_settings(company):
	"""A missing configuration is always disabled; returns only an enabled record."""
	if not isinstance(company, str) or not company or len(company) > 140:
		frappe.throw(_("Customer App is not available."), frappe.PermissionError)
	row = frappe.db.get_value(
		"Customer App Settings",
		{"company": company},
		["name", "enable_customer_app"],
		as_dict=True,
	)
	if not row or not cint(row.enable_customer_app):
		frappe.throw(_("Customer App is not available."), frappe.PermissionError)
	return row.name


def enabled_workshop(company, workshop):
	"""Validate new-booking availability server-side, independent of Desk."""
	settings_name = enabled_settings(company)
	if frappe.db.get_value("Service Workshop", workshop, "company") != company:
		frappe.throw(_("Workshop is not available for Customer App booking."), frappe.PermissionError)
	if not frappe.db.exists(
		"Customer App Workshop Availability",
		{
			"parenttype": "Customer App Settings",
			"parent": settings_name,
			"parentfield": "workshops",
			"workshop": workshop,
			"booking_enabled": 1,
		},
	):
		frappe.throw(_("Workshop is not available for Customer App booking."), frappe.PermissionError)
	return workshop


def authorized_customers(company, user=None):
	"""Only active, VERIFIED company-specific links; no email-only account guessing."""
	enabled_settings(company)
	user = user or frappe.session.user
	if user == "Guest":
		frappe.throw(_("Sign in to access the Customer App."), frappe.PermissionError)
	return set(
		frappe.get_all(
			"Customer App Account",
			filters={"company": company, "user": user, "verified": 1, "enabled": 1},
			pluck="customer",
		)
	)


def require_customers(company):
	customers = authorized_customers(company)
	if not customers:
		frappe.throw(_("Your Customer App account is not yet verified for this company."), frappe.PermissionError)
	return sorted(customers)
