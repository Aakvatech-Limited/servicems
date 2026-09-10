# Copyright (c) 2022, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		return

	columns = [
		{"fieldname": "customer", "fieldtype": "Data", "label": _("Customer")},
	]

	if not filters.customer_view:
		columns.append(
			{
				"fieldname": "service_item_name",
				"fieldtype": "Data",
				"label": _("Service Item"),
			}
		)

	columns.append({"fieldname": "count", "fieldtype": "Int", "label": _("No. of Bills")})

	columns.append(
		{
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"label": _("Total Amount"),
		}
	)

	if not filters.customer_view:
		data = frappe.get_list(
			"Service Job Card",
			filters=[
				["receiving_datetime", "between", [filters.from_date, filters.to_date]],
				["docstatus", "=", 1],
			],
			fields=[
				"customer",
				"service_item_name",
				"count(service_item_name) as count",
				"sum(total) as total_amount",
			],
			group_by="service_item_name",
		)
	else:
		data = frappe.get_list(
			"Service Job Card",
			filters=[
				["receiving_datetime", "between", [filters.from_date, filters.to_date]],
				["docstatus", "=", 1],
			],
			fields=[
				"customer",
				"count(service_item_name) as count",
				"sum(total) as total_amount",
			],
			group_by="customer",
		)

	return columns, data
