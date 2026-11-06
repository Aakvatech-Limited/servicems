"""Per-company Customer App configuration. The feature is opt-in and lossless."""

import re

import frappe
from frappe import _
from frappe.model.document import Document

from servicems.customer_app.security import can_manage_company


class CustomerAppSettings(Document):
	def validate(self):
		if not can_manage_company(self.company):
			frappe.throw(_("You cannot configure this company's Customer App."), frappe.PermissionError)

		previous = self.get_doc_before_save()
		if previous and previous.company != self.company:
			frappe.throw(_("Customer App company cannot be changed."))

		if self.registration_policy not in ("Invitation Only", "Hybrid"):
			frappe.throw(_("Select Invitation Only or Hybrid registration."))

		for field in ("primary_color", "secondary_color", "navbar_color"):
			value = self.get(field)
			if value and not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
				frappe.throw(_("{0} must be a six-digit hex colour.").format(field))

		seen = set()
		for entry in self.workshops:
			if entry.workshop in seen:
				frappe.throw(_("A workshop can only appear once."))
			seen.add(entry.workshop)
			workshop_company = frappe.db.get_value("Service Workshop", entry.workshop, "company")
			if not workshop_company or workshop_company != self.company:
				frappe.throw(_("All Customer App workshops must belong to the selected company."))
