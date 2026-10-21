# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from erpnext.controllers.queries import item_query
from frappe.model.document import Document


class ServiceSettings(Document):
	def on_update(self):
		from servicems.navigation import sync_bay_navigation

		sync_bay_navigation()


@frappe.whitelist()
def get_filtered_items(doctype, txt, searchfield, start, page_len, filters):
	doc = frappe.get_single("Service Settings")
	groups = [i.item_group for i in doc.item_groups]
	filters = {"item_group": ["in", groups]}
	items = item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False)
	return items
