import frappe

from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import PART_ITEM, SOLD_BY

NAMED_BY_FIELD = [
	("Job Card Status", "status_name", "_Test SMS Status"),
	("Service Task", "task_name", "_Test SMS Task C"),
	("Sold By", "sold_by", "_Test SMS Dealer Two"),
	("Vehicle Make", "make", "_Test SMS Make Two"),
	("Service Vehicle Type", "vehicle_type", "_Test SMS Type Two"),
]


class TestSimpleMasters(ServiceMSTestCase):
	def test_masters_named_by_field(self):
		for doctype, fieldname, value in NAMED_BY_FIELD:
			doc = frappe.get_doc({"doctype": doctype, fieldname: value}).insert()
			self.assertEqual(doc.name, value, doctype)
			duplicate = frappe.get_doc({"doctype": doctype, fieldname: value})
			self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)

	def test_parts_and_consumable(self):
		doc = frappe.get_doc(
			{"doctype": "Parts and Consumable", "part_name": "_Test SMS Filter", "item": PART_ITEM}
		).insert()
		self.assertEqual(doc.name, "_Test SMS Filter")

	def test_sold_by_fixture(self):
		self.assertEqual(frappe.get_doc("Sold By", SOLD_BY).sold_by, SOLD_BY)
