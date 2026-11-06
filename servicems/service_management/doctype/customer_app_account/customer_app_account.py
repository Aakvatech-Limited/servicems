"""Explicit verified company/customer/User link for Customer App access."""

import frappe
from frappe import _
from frappe.model.document import Document

from servicems.customer_app.security import can_manage_company


class CustomerAppAccount(Document):
	def validate(self):
		if not can_manage_company(self.company):
			frappe.throw(_("You cannot manage Customer App users for this company."), frappe.PermissionError)

		previous = self.get_doc_before_save()
		if previous and (previous.company != self.company or previous.customer != self.customer or previous.user != self.user):
			frappe.throw(_("Company, Customer and User cannot be changed; revoke and create a new link."))

		other = frappe.db.exists(
			"Customer App Account",
			{"company": self.company, "customer": self.customer, "user": self.user, "name": ["!=", self.name or ""]},
		)
		if other:
			frappe.throw(_("This Customer App account link already exists."))

		if self.verified:
			if frappe.db.get_value("User", self.user, "user_type") != "Website User":
				frappe.throw(_("Customer App account must belong to a Website User."))
			if not frappe.db.exists(
				"Portal User", {"parenttype": "Customer", "parent": self.customer, "user": self.user}
			):
				frappe.throw(_("Verify the Customer's ERPNext Portal User relationship first."))
