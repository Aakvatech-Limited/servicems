import frappe
from pypika.terms import Not
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from frappe.utils.change_log import get_app_branch
from frappe.desk.search import search_link, search_widget, build_for_autosuggest

__app_version = {}


@frappe.whitelist()
def search_link(
	doctype,
	txt,
	query=None,
	filters=None,
	page_length=20,
	searchfield=None,
	reference_doctype=None,
	ignore_user_permissions=False,
):
    if not __app_version.get("frappe"):
        __app_version["frappe"] = get_app_branch("frappe")

    if not __app_version.get("frappe"):
        return search_link(
            doctype,
            txt,
            query=None,
            filters=None,
            page_length=20,
            searchfield=None,
            reference_doctype=None,
            ignore_user_permissions=False,
        )
    
    elif __app_version.get("frappe") in ["version-14", "version-13", "version-12"]:
        search_widget(
            doctype,
            txt.strip(),
            query,
            searchfield=searchfield,
            page_length=page_length,
            filters=filters,
            reference_doctype=reference_doctype,
            ignore_user_permissions=ignore_user_permissions,
        )
        frappe.response["results"] = build_for_autosuggest(frappe.response["values"], doctype=doctype)
        del frappe.response["values"]
        return frappe.response["results"]
    
    else:
        return search_link(
            doctype,
            txt,
            query=None,
            filters=None,
            page_length=20,
            searchfield=None,
            reference_doctype=None,
            ignore_user_permissions=False,
        )


@frappe.whitelist()
def get_service_bays(): 
    filters = frappe.request.args.to_dict()
    
    b = DocType("Bay")
    sb = DocType("Service Booking")
    
    sb_query = (
		frappe.qb.from_(sb)
		.select(
			sb.status,
			sb.workshop,
			sb.customer,
			sb.booking_time,
			sb.booking_date,
			sb.service_vehicle,
			sb.bay.as_("bay_name"),
			sb.name.as_("booking_id"),
            Count(sb.bay).as_("count")
		)
		.where(sb.status.isin(["Pending", "In Progress"]))
        .groupby(sb.bay)
		.orderby(sb.bay, sb.booking_date, sb.booking_time)
	)
    
    if filters.get("from_date"):
        sb_query = sb_query.where(sb.booking_date >= filters.get("from_date"))
    
    if filters.get("to_date"):
        sb_query = sb_query.where(sb.booking_date <= filters.get("to_date"))
    
    if filters.get("workshop"):
        sb_query = sb_query.where(sb.workshop == filters.get("workshop"))
    
    sb_data = sb_query.run(as_dict=True)
    
    bay_names = [bay.bay_name for bay in sb_data]
    
    bays_query = (
		frappe.qb.from_(b)
		.select(
			b.name.as_("bay_name"),
			b.service_workshop.as_("workshop"),
		)
		.orderby(b.name)
	)
    
    if filters.get("workshop"):
        bays_query = bays_query.where(b.service_workshop == filters.get("workshop"))
    
    if len(bay_names) > 0:
        bays_query = bays_query.where(Not(b.name.isin(bay_names)))
    
    bays = bays_query.run(as_dict=True)
    
    sb_data.extend(bays)
    
    bays_data = sorted(sb_data, key=lambda x: x.get("bay_name"))
    
    return bays_data


@frappe.whitelist()
def create_quotation(job_card_id):
    items = []
    job_card_doc = frappe.get_doc("Service Job Card", job_card_id)
    warehouse = frappe.get_cached_value("Service Workshop", job_card_doc.workshop, "workshop_warehouse")

    quo_doc = frappe.new_doc("Quotation")
    quo_doc.company = job_card_doc.company
    quo_doc.quotation_to = "Customer"
    quo_doc.party_name = job_card_doc.customer
    quo_doc.order_type = "Sales"
    quo_doc.items = []


    for service in job_card_doc.services:
        if not service.is_billable:
            continue

        quo_doc.append("items", {
            "item_code": service.item,
            "qty": 1,
            "rate": service.rate or 0,
            "warehouse": warehouse,
            "stock_uom": frappe.get_cached_value("Item", service.item, "stock_uom"),
        })

    for part in job_card_doc.supplied_parts:
        if not part.is_billable or part.is_return or part.qty == 0:
            continue

        quo_doc.append("items", {
            "item_code": part.item,
            "qty": part.qty,
            "rate": part.rate or 0,
            "warehouse": warehouse,
            "stock_uom": frappe.get_cached_value("Item", part.item, "stock_uom"),
        })
    
    quo_doc.run_method("set_missing_values")
    quo_doc.run_method("calculate_taxes_and_totals")
    frappe.flags.ignore_permissions = True
    quo_doc.save()

    job_card_doc.quotation = quo_doc.name
    job_card_doc.save()
    job_card_doc.reload()
    
    return quo_doc.name
