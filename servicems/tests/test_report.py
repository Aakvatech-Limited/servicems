import frappe

from servicems.service_management.report.service_job_card_detail.service_job_card_detail import execute
from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	COMPANY,
	CUSTOMER,
	CUSTOMER_WITH_PRICE_LIST,
	FREE_SERVICE_TEMPLATE,
	PART_RATE,
	SERVICE_RATE,
	TEMPLATE_PART_QTY,
	VEHICLE,
	VEHICLE_2,
	complete_tasks,
	make_job_card,
)

REPORT_DATETIME = "2020-01-15 10:00:00"


def submit_job_card(**kwargs):
	job_card = make_job_card(receiving_datetime=REPORT_DATETIME, **kwargs)
	complete_tasks(job_card)
	job_card.save()
	job_card.submit()
	return job_card


def run(customer_view=0):
	filters = frappe._dict(from_date="2020-01-14", to_date="2020-01-16", customer_view=customer_view)
	return execute(filters)


class TestServiceJobCardDetailReport(ServiceMSTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_value("Company Service Management Settings", COMPANY, "use_parts_entry", 1)

	def test_without_filters(self):
		self.assertIsNone(execute(None))

	def test_vehicle_view(self):
		submit_job_card()
		submit_job_card(services=(FREE_SERVICE_TEMPLATE,))
		submit_job_card(customer=CUSTOMER_WITH_PRICE_LIST, vehicle=VEHICLE_2)
		columns, data = run()
		self.assertEqual(
			[column["fieldname"] for column in columns],
			["customer", "service_item_name", "count", "total_amount"],
		)
		rows = {row["service_item_name"]: row for row in data}
		self.assertEqual(rows[VEHICLE]["count"], 2)
		self.assertEqual(rows[VEHICLE]["total_amount"], SERVICE_RATE + PART_RATE * TEMPLATE_PART_QTY)
		self.assertEqual(rows[VEHICLE_2]["customer"], CUSTOMER_WITH_PRICE_LIST)

	def test_customer_view(self):
		submit_job_card()
		submit_job_card(services=(FREE_SERVICE_TEMPLATE,))
		columns, data = run(customer_view=1)
		self.assertEqual([column["fieldname"] for column in columns], ["customer", "count", "total_amount"])
		rows = {row["customer"]: row for row in data}
		self.assertEqual(rows[CUSTOMER]["count"], 2)

	def test_draft_job_cards_are_excluded(self):
		make_job_card(receiving_datetime=REPORT_DATETIME)
		_, data = run()
		self.assertEqual(data, [])

	def test_report_record(self):
		report = frappe.get_doc("Report", "Service Job Card Detail")
		self.assertEqual(
			(report.report_type, report.ref_doctype, report.is_standard),
			("Script Report", "Service Job Card", "Yes"),
		)
