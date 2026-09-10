import frappe
from frappe.utils import add_days, nowdate, set_request

from servicems.api.api import (
	create_quotation,
	get_service_bays,
	get_service_transaction_company,
	search_link_data,
)
from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	BAY,
	BAY_2,
	COMPANY,
	CUSTOMER,
	FREE_SERVICE_TEMPLATE,
	PART_ITEM,
	PART_RATE,
	SERVICE_ITEM,
	SERVICE_RATE,
	SERVICE_TEMPLATE,
	TEMPLATE_PART_QTY,
	VEHICLE,
	VEHICLE_2,
	WORKSHOP,
	WORKSHOP_WAREHOUSE,
	make_booking,
	make_job_card,
	receive_stock,
)

ISOLATED_WORKSHOP = "_Test SMS Bays Workshop"
ISOLATED_BAYS = ("_Test SMS Iso Bay 1", "_Test SMS Iso Bay 2")


def bays(**query):
	"""Query bays of a workshop created per test so data seeded by other suites cannot interfere."""
	query.setdefault("workshop", ISOLATED_WORKSHOP)
	set_request(path="/api/method/servicems.api.api.get_service_bays", query_string=query)
	return {row["bay_name"]: row for row in get_service_bays()}


def make_isolated_workshop():
	frappe.get_doc(
		{
			"doctype": "Service Workshop",
			"workshop_name": ISOLATED_WORKSHOP,
			"company": COMPANY,
			"parts_warehouse": frappe.db.get_value("Service Workshop", WORKSHOP, "parts_warehouse"),
			"workshop_warehouse": frappe.db.get_value("Service Workshop", WORKSHOP, "workshop_warehouse"),
		}
	).insert()
	for bay in ISOLATED_BAYS:
		frappe.get_doc({"doctype": "Bay", "bay": bay, "service_workshop": ISOLATED_WORKSHOP}).insert()


class TestTransactionCompany(ServiceMSTestCase):
	def test_service_settings_company_wins(self):
		self.assertEqual(get_service_transaction_company("Other"), COMPANY)

	def test_fallback_without_settings(self):
		frappe.db.set_single_value("Service Settings", "company", None)
		self.assertEqual(get_service_transaction_company("Other"), "Other")
		self.assertIsNone(get_service_transaction_company())


class TestSearchLinkData(ServiceMSTestCase):
	def test_returns_link_results(self):
		results = search_link_data("Service Workshop", "_Test SMS")
		self.assertIn(WORKSHOP, [row["value"] for row in results])

	def test_empty_text_returns_results(self):
		results = search_link_data("Bay", "")
		self.assertTrue({BAY, BAY_2} <= {row["value"] for row in results})

	def test_filters_are_applied(self):
		results = search_link_data("Bay", "", filters={"service_workshop": "_Test SMS Missing Workshop"})
		self.assertEqual(results, [])
		results = search_link_data("Bay", "", filters={"service_workshop": WORKSHOP})
		self.assertTrue({BAY, BAY_2} <= {row["value"] for row in results})

	def test_is_whitelisted(self):
		for method in (search_link_data, get_service_bays, create_quotation):
			self.assertIn(method, frappe.whitelisted)


class TestGetServiceBays(ServiceMSTestCase):
	def setUp(self):
		super().setUp()
		make_isolated_workshop()

	def book(self, **kwargs):
		kwargs.setdefault("bay", ISOLATED_BAYS[0])
		kwargs.setdefault("workshop", ISOLATED_WORKSHOP)
		return make_booking(**kwargs)

	def test_lists_free_bays(self):
		data = bays()
		self.assertEqual(set(data), set(ISOLATED_BAYS))
		self.assertEqual(data[ISOLATED_BAYS[0]]["workshop"], ISOLATED_WORKSHOP)
		self.assertNotIn("booking_id", data[ISOLATED_BAYS[0]])

	def test_lists_booked_bays_with_booking(self):
		booking = self.book()
		data = bays()
		row = data[ISOLATED_BAYS[0]]
		self.assertEqual(row["booking_id"], booking.name)
		self.assertEqual(
			(row["status"], row["customer"], row["service_vehicle"]), ("Pending", CUSTOMER, VEHICLE)
		)
		self.assertEqual(row["count"], 1)
		self.assertNotIn("booking_id", data[ISOLATED_BAYS[1]])

	def test_closed_bookings_are_ignored(self):
		self.book().close_booking()
		self.assertNotIn("booking_id", bays()[ISOLATED_BAYS[0]])

	def test_date_and_vehicle_filters(self):
		booking_date = add_days(nowdate(), 3)
		self.book(booking_date=booking_date)
		bay = ISOLATED_BAYS[0]
		self.assertIn("booking_id", bays(from_date=booking_date, to_date=booking_date)[bay])
		self.assertNotIn("booking_id", bays(from_date=add_days(booking_date, 1))[bay])
		self.assertNotIn("booking_id", bays(to_date=add_days(booking_date, -1))[bay])
		self.assertIn("booking_id", bays(vehicle=VEHICLE)[bay])
		self.assertNotIn("booking_id", bays(vehicle=VEHICLE_2)[bay])

	def test_without_workshop_filter_lists_every_bay(self):
		set_request(path="/api/method/servicems.api.api.get_service_bays", query_string={})
		names = {row["bay_name"] for row in get_service_bays()}
		self.assertTrue({BAY, BAY_2, *ISOLATED_BAYS} <= names)
		self.assertEqual(bays(workshop="_Test SMS Missing Workshop"), {})


class TestCreateQuotation(ServiceMSTestCase):
	def test_quotation_from_services_and_supplied_parts(self):
		receive_stock(PART_ITEM)
		job_card = make_job_card()
		job_card.create_stock_entry("call")

		quotation_name = create_quotation(job_card.name)
		quotation = frappe.get_doc("Quotation", quotation_name)
		self.assertEqual(
			(quotation.quotation_to, quotation.party_name, quotation.company), ("Customer", CUSTOMER, COMPANY)
		)
		self.assertEqual(quotation.service_job_card, job_card.name)
		items = {row.item_code: row for row in quotation.items}
		self.assertEqual(set(items), {SERVICE_ITEM, PART_ITEM})
		self.assertEqual((items[SERVICE_ITEM].qty, items[SERVICE_ITEM].rate), (1, SERVICE_RATE))
		self.assertEqual(
			(items[PART_ITEM].qty, items[PART_ITEM].rate, items[PART_ITEM].warehouse),
			(TEMPLATE_PART_QTY, PART_RATE, WORKSHOP_WAREHOUSE),
		)
		self.assertEqual(quotation.net_total, SERVICE_RATE + PART_RATE * TEMPLATE_PART_QTY)
		self.assertEqual(frappe.db.get_value("Service Job Card", job_card.name, "quotation"), quotation_name)

	def test_does_not_leak_ignore_permissions_flag(self):
		frappe.flags.ignore_permissions = False
		create_quotation(make_job_card().name)
		self.assertFalse(frappe.flags.ignore_permissions)

	def test_non_billable_rows_are_excluded(self):
		job_card = make_job_card(services=(FREE_SERVICE_TEMPLATE, SERVICE_TEMPLATE))
		quotation = frappe.get_doc("Quotation", create_quotation(job_card.name))
		self.assertEqual([row.item_code for row in quotation.items], [SERVICE_ITEM])
