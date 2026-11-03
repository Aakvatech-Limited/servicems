"""Additive, idempotent ERPNext integration metadata; never rewrite transactions."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def field(name, label, fieldtype="Data", **kwargs):
	return {"fieldname": name, "label": label, "fieldtype": fieldtype, **kwargs}


def execute():
	create_custom_fields(
		{
			"Stock Entry": [
				field(
					"service_parts_operation",
					"Service Parts Operation",
					"Select",
					options="\nIssue\nConsume\nReturn",
				),
				field("service_posting_request", "Service Posting Request", read_only=1, no_copy=1),
				field("service_request_payload", "Service Request Payload", "Long Text", hidden=1, no_copy=1),
			],
			"Stock Entry Detail": [
				field("service_issue_entry", "Service Source Issue", "Link", options="Stock Entry"),
				field("service_issue_detail", "Service Source Issue Row"),
				field("service_part_row", "Service Planned Part Row", read_only=1),
			],
			"Sales Invoice Item": [
				field("service_billing_key", "Service Billing Key", read_only=1),
				field(
					"service_issue_entry", "Service Source Issue", "Link", options="Stock Entry", read_only=1
				),
				field("service_issue_detail", "Service Source Issue Row", read_only=1),
			],
			"Quotation Item": [field("service_billing_key", "Service Billing Key", read_only=1)],
			"Purchase Invoice Item": [
				field("service_job_card", "Service Job Card", "Link", options="Service Job Card")
			],
			"Purchase Order Item": [
				field("service_job_card", "Service Job Card", "Link", options="Service Job Card")
			],
		}
	)
