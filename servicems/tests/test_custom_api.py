import frappe
from frappe.utils import add_days, nowdate

from servicems.custom_api import get_item_info
from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import PARTS_ITEM_GROUP, PARTS_WAREHOUSE, WORKSHOP_WAREHOUSE, receive_stock

BATCH_ITEM = "_Test SMS Batch Part"
BATCH = "_TSMS-B1"


def make_batch_item():
	make_item(BATCH_ITEM, has_batch_no=1)
	if not frappe.db.exists("Batch", BATCH):
		frappe.get_doc(
			{
				"doctype": "Batch",
				"batch_id": BATCH,
				"item": BATCH_ITEM,
				"expiry_date": add_days(nowdate(), 30),
			}
		).insert()


INFO_ITEM = "_Test SMS Info Part"


def make_item(item_code, **values):
	if not frappe.db.exists("Item", item_code):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_code,
				"item_group": PARTS_ITEM_GROUP,
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"valuation_rate": 10,
				**values,
			}
		).insert()


class TestGetItemInfo(ServiceMSTestCase):
	def test_stock_per_warehouse(self):
		make_item(INFO_ITEM)
		receive_stock(INFO_ITEM, qty=10, warehouse=PARTS_WAREHOUSE)
		receive_stock(INFO_ITEM, qty=4, warehouse=WORKSHOP_WAREHOUSE)
		rows = {row["warehouse"]: row for row in get_item_info(INFO_ITEM)}
		self.assertEqual(rows[PARTS_WAREHOUSE]["actual_qty"], 10)
		self.assertEqual(rows[WORKSHOP_WAREHOUSE]["actual_qty"], 4)
		self.assertEqual(rows[PARTS_WAREHOUSE]["stock_uom"], "Nos")
		self.assertFalse(rows[PARTS_WAREHOUSE]["batch_no"])
		self.assertIsNone(rows[PARTS_WAREHOUSE]["expires_on"])

	def test_latest_balance_is_used(self):
		make_item(INFO_ITEM)
		receive_stock(INFO_ITEM, qty=5)
		receive_stock(INFO_ITEM, qty=7)
		rows = get_item_info(INFO_ITEM)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["actual_qty"], 12)

	def test_item_without_stock(self):
		self.assertEqual(get_item_info("_Test SMS Missing Item"), [])

	def test_batch_expiry(self):
		frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
		frappe.db.set_single_value("Stock Settings", "use_serial_batch_fields", 1)
		make_batch_item()
		receive_stock(BATCH_ITEM, qty=3, batch_no=BATCH)
		rows = get_item_info(BATCH_ITEM)
		self.assertEqual(len(rows), 1)
		self.assertEqual((rows[0]["batch_no"], rows[0]["actual_qty"]), (BATCH, 3))
		self.assertEqual(str(rows[0]["expires_on"]), add_days(nowdate(), 30))
		self.assertEqual(rows[0]["expiry_status"], 30)
