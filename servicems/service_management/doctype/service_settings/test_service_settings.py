# Copyright (c) 2021, Aakvatech Limited and Contributors
# See license.txt

import frappe
from frappe.desk.search import search_widget

from servicems.service_management.doctype.service_settings.service_settings import get_filtered_items
from servicems.tests.base import ServiceMSTestCase
from servicems.tests.utils import (
	COMPANY,
	IGNORE_TEST_RECORD_DEPENDENCIES,
	PART_ITEM,
	PART_ITEM_2,
	PARTS_ITEM_GROUP,
	PRICE_LIST,
	SERVICE_ITEM,
)

IGNORE_TEST_RECORD_DEPENDENCIES = IGNORE_TEST_RECORD_DEPENDENCIES
QUERY = "servicems.service_management.doctype.service_settings.service_settings.get_filtered_items"


class TestServiceSettings(ServiceMSTestCase):
	def test_settings_values(self):
		settings = frappe.get_single("Service Settings")
		self.assertEqual((settings.company, settings.price_list), (COMPANY, PRICE_LIST))
		self.assertEqual([row.item_group for row in settings.item_groups], [PARTS_ITEM_GROUP])

	def test_price_list_is_mandatory(self):
		settings = frappe.get_single("Service Settings")
		settings.price_list = None
		self.assertRaises(frappe.MandatoryError, settings.save)

	def test_filtered_items_only_from_configured_groups(self):
		items = [row[0] for row in get_filtered_items("Item", "_Test SMS", "name", 0, 20, {})]
		self.assertIn(PART_ITEM, items)
		self.assertIn(PART_ITEM_2, items)
		self.assertNotIn(SERVICE_ITEM, items)

	def test_query_works_through_link_search(self):
		results = search_widget("Item", "_Test SMS", query=QUERY, page_length=20)
		values = [row[0] for row in results]
		self.assertIn(PART_ITEM, values)
		self.assertNotIn(SERVICE_ITEM, values)
