# Copyright (c) 2022, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ServiceVehicleInspection(Document):
	def validate(self):
		if self.inspection_status != "Completed":
			return
		if not self.service_job_card or not self.inspection_stage:
			frappe.throw(_("A completed inspection requires a Job Card and inspection stage."))
		if not self.inspection_template:
			frappe.throw(_("Select an inspection template before completion."))
		requires_photos = frappe.db.get_value(
			"Service Pre Inspection Template", self.inspection_template, "require_photographs"
		)
		if requires_photos:
			attached = bool(self.image_upload)
			if not attached and not self.is_new():
				attached = bool(frappe.db.exists("File", {
					"attached_to_doctype": self.doctype,
					"attached_to_name": self.name,
					"is_folder": 0,
				}))
			if not attached:
				frappe.throw(_("Attach at least one inspection photograph before completion."))
