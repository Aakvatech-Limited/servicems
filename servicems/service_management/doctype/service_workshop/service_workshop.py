# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ServiceWorkshop(Document):
	def validate(self):
		service_company = frappe.db.get_single_value("Service Settings", "company")
		default_company = frappe.defaults.get_global_default("company")
		self.company = service_company or default_company or self.company
