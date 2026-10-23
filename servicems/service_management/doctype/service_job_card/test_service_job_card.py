# Copyright (c) 2026, Aakvatech Limited
import unittest
from unittest.mock import patch

import frappe
from servicems.service_management.doctype.service_job_card.service_job_card import ServiceJobCard, reconcile_parts_quantities


class TestServiceJobCard(unittest.TestCase):
	def test_phase_one_metadata(self):
		meta = frappe.get_meta("Service Job Card")
		self.assertEqual(meta.get_field("labour_entries").options, "Service Labour Entry")
		self.assertIsNotNone(meta.get_field("quality_check_confirmed"))
		self.assertIsNotNone(meta.get_field("overview_tab"))

	def test_qc_required_on_new_completion(self):
		card = ServiceJobCard({"doctype": "Service Job Card", "status": "Completed", "quality_check_confirmed": 0})
		with patch.object(frappe.db, "get_single_value", return_value=1):
			with self.assertRaises(frappe.ValidationError):
				card.validate_quality_check()

	def test_qc_optional_for_new_completion(self):
		card = ServiceJobCard({"doctype": "Service Job Card", "status": "Completed", "quality_check_confirmed": 0})
		with patch.object(frappe.db, "get_single_value", return_value=0):
			card.validate_quality_check()

	def test_stock_transfer_rejects_missing_warehouses(self):
		from types import SimpleNamespace
		card = ServiceJobCard({"doctype": "Service Job Card"})
		workshop = SimpleNamespace(parts_warehouse=None, workshop_warehouse="WORKSHOP")
		with self.assertRaises(frappe.ValidationError):
			card.validate_stock_transfer_configuration(workshop, "Example Co")

	def test_stock_transfer_rejects_same_warehouse(self):
		from types import SimpleNamespace
		card = ServiceJobCard({"doctype": "Service Job Card"})
		workshop = SimpleNamespace(parts_warehouse="STORES", workshop_warehouse="STORES")
		with self.assertRaises(frappe.ValidationError):
			card.validate_stock_transfer_configuration(workshop, "Example Co")

	def test_stock_transfer_rejects_wrong_company(self):
		from types import SimpleNamespace
		card = ServiceJobCard({"doctype": "Service Job Card"})
		workshop = SimpleNamespace(parts_warehouse="STORES", workshop_warehouse="WORKSHOP")
		with patch.object(frappe.db, "get_value", return_value="Other Co"):
			with self.assertRaises(frappe.ValidationError):
				card.validate_stock_transfer_configuration(workshop, "Example Co")

	def test_stock_transfer_accepts_matching_company(self):
		from types import SimpleNamespace
		card = ServiceJobCard({"doctype": "Service Job Card"})
		workshop = SimpleNamespace(parts_warehouse="STORES", workshop_warehouse="WORKSHOP")
		with patch.object(frappe.db, "get_value", return_value="Example Co") as lookup:
			card.validate_stock_transfer_configuration(workshop, "Example Co")
			self.assertEqual(lookup.call_count, 2)

	def test_parts_reconciliation_exact(self):
		result = reconcile_parts_quantities(10, 7, 2)
		self.assertEqual(result["outstanding"], 1)

	def test_parts_reconciliation_fully_allocated(self):
		self.assertEqual(reconcile_parts_quantities(10, 7, 3)["outstanding"], 0)

	def test_parts_reconciliation_rejects_overconsumption(self):
		with self.assertRaises(frappe.ValidationError):
			reconcile_parts_quantities(10, 11, 0)

	def test_parts_reconciliation_rejects_excess_returns(self):
		with self.assertRaises(frappe.ValidationError):
			reconcile_parts_quantities(10, 7, 4)

	def test_parts_reconciliation_rejects_negative(self):
		with self.assertRaises(frappe.ValidationError):
			reconcile_parts_quantities(-1, 0, 0)
