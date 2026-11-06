"""Field technician access, limited to assigned ServiceMS Job Cards.

Assignments may be standard Frappe ToDos or labour entries for an Employee
linked to the authenticated user. Do not use a blanket System Manager role.
"""

import frappe

FIELD_ROLE = "ServiceMS Field Technician"
JOB_CARD = "Service Job Card"
INSPECTION = "Service Vehicle Inspection"


def _field_user(user=None):
	user = user or frappe.session.user
	return (
		user != "Guest"
		and FIELD_ROLE in frappe.get_roles(user)
		and "System Manager" not in frappe.get_roles(user)
	)


def _assignment_condition(user):
	escaped = frappe.db.escape(user)
	return (
		"("
		"name IN (SELECT t.reference_name FROM `tabToDo` t "
		"WHERE t.reference_type='Service Job Card' AND t.allocated_to=" + escaped + " AND t.status = 'Open')"
		" OR name IN (SELECT l.parent FROM `tabService Labour Entry` l "
		"JOIN `tabEmployee` e ON e.name=l.technician "
		"WHERE l.parenttype='Service Job Card' AND l.docstatus < 2 AND e.status='Active' AND e.user_id="
		+ escaped
		+ ")"
		")"
	)


def field_job_query(user=None):
	user = user or frappe.session.user
	if not _field_user(user):
		return ""
	return _assignment_condition(user).replace("name IN", "`tabService Job Card`.name IN")


def field_inspection_query(user=None):
	user = user or frappe.session.user
	if not _field_user(user):
		return ""
	# Only inspections of Job Cards assigned to the technician.
	assigned = _assignment_condition(user)
	return (
		"`tabService Vehicle Inspection`.service_job_card IN "
		"(SELECT name FROM `tabService Job Card` WHERE " + assigned + ")"
	)


def _assigned(job_card, user):
	if not job_card or not user:
		return False
	if frappe.db.exists(
		"ToDo",
		{
			"reference_type": JOB_CARD,
			"reference_name": job_card,
			"allocated_to": user,
			"status": "Open",
		},
	):
		return True
	return bool(
		frappe.db.sql(
			"""select l.name from `tabService Labour Entry` l
            join `tabEmployee` e on e.name=l.technician
            where l.parenttype='Service Job Card' and l.docstatus < 2 and e.status='Active'
            and l.parent=%s and e.user_id=%s
            limit 1""",
			(job_card, user),
		)
	)


def job_card_permission(doc, user=None, ptype=None, permission_type=None):
	user = user or frappe.session.user
	if not _field_user(user):
		return True
	if (ptype or permission_type) not in ("read", "select"):
		return False
	if not doc:
		return True
	return _assigned(doc.name, user)


def inspection_permission(doc, user=None, ptype=None, permission_type=None):
	user = user or frappe.session.user
	if not _field_user(user):
		return True
	if (ptype or permission_type) not in ("read", "write", "create", "select"):
		return False
	if doc is None:
		return (ptype or permission_type) == "create"
	return _assigned(doc.service_job_card, user)


def file_permission(doc, user=None, ptype=None):
	if not _field_user(user) or doc.attached_to_doctype != INSPECTION:
		return True
	job_card = frappe.db.get_value(INSPECTION, doc.attached_to_name, "service_job_card")
	return _assigned(job_card, user or frappe.session.user)


def ensure_field_permissions():
	"""Idempotent permission setup; executed on install and after migration."""
	previous = frappe.flags.in_migrate
	frappe.flags.in_migrate = True
	try:
		_set_field_permissions()
	finally:
		frappe.flags.in_migrate = previous


def _set_field_permissions():
	# Dependent-access hooks must not expand the technician's three audited grants.
	role = FIELD_ROLE
	if not frappe.db.exists("Role", role):
		frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 0}).insert(
			ignore_permissions=True
		)
	from frappe import permissions

	for doctype, rights in (
		(JOB_CARD, ("read",)),
		(INSPECTION, ("read", "write", "create")),
		("Service Pre Inspection Template", ("read",)),
	):
		if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
			permissions.add_permission(doctype, role, 0)
		for field in ("read", "write", "create", "delete", "submit", "cancel", "amend"):
			permissions.update_permission_property(doctype, role, 0, field, int(field in rights))
