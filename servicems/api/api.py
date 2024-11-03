import frappe
from pypika.terms import Not
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from frappe.utils.change_log import get_app_branch
from frappe.desk.search import search_link, search_widget, build_for_autosuggest


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
    app_version = get_app_branch("frappe")
    if not app_version:
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
    
    elif app_version in ["version-14", "version-13", "version-12"]:
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
