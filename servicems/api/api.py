import frappe
from frappe.desk.search import build_for_autosuggest, search_link, search_widget
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from frappe.utils import cint
from pypika.terms import Not


def get_service_transaction_company(fallback_company=None):
	company = frappe.db.get_single_value("Service Settings", "company")
	return company or fallback_company


@frappe.whitelist()
def search_link_data(
	doctype,
	txt,
	query=None,
	filters=None,
	page_length=20,
	searchfield=None,
	reference_doctype=None,
	ignore_user_permissions=False,
):
	frappe_version = frappe.__version__.split(".")[0]

	if frappe_version and cint(frappe_version) in [12, 13, 14]:
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
			Count(sb.bay).as_("count"),
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

	if filters.get("vehicle"):
		sb_query = sb_query.where(sb.service_vehicle == filters.get("vehicle"))

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
	from servicems.billing import make_quotation

	return make_quotation(job_card_id)
