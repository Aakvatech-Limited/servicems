# Copyright (c) 2022, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Sum


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

	return columns, get_data(filters)


def get_data(filters):
	job_card = frappe.qb.DocType("Service Job Card")
	group_by = job_card.customer if filters.customer_view else job_card.service_item_name

	query = (
		frappe.qb.from_(job_card)
		.select(
			job_card.customer,
			Count(job_card.service_item_name).as_("count"),
			Sum(job_card.total).as_("total_amount"),
		)
		.where(job_card.docstatus == 1)
		.where(job_card.receiving_datetime[filters.from_date : filters.to_date])
		.groupby(group_by)
	)

	if not filters.customer_view:
		query = query.select(job_card.service_item_name)

	return query.run(as_dict=True)
