"""Focused Customer App security regression tests.

These use Frappe's database where available and mocks for fail-closed guards.
"""

import unittest
from unittest.mock import patch

import frappe

from servicems.customer_app import api, security


class TestCustomerAppSecurity(unittest.TestCase):
	def test_guest_has_no_customer_access(self):
		with patch.object(security, "enabled_settings", return_value="SETTINGS"), patch.object(
			frappe.session, "user", "Guest"
		):
			with self.assertRaises(frappe.PermissionError):
				security.authorized_customers("Example Company")

	def test_disabled_company_blocks_access(self):
		with patch.object(frappe.db, "get_value", return_value=None):
			with self.assertRaises(frappe.PermissionError):
				security.enabled_settings("Example Company")

	def test_missing_workshop_permission_defaults_to_disabled(self):
		with patch.object(security, "enabled_settings", return_value="SETTINGS"), patch.object(
			frappe.db, "get_value", return_value="Company A"
		), patch.object(frappe.db, "exists", return_value=None):
			with self.assertRaises(frappe.PermissionError):
				security.enabled_workshop("Company A", "Workshop A")

	def test_other_company_workshop_is_rejected(self):
		with patch.object(security, "enabled_settings", return_value="SETTINGS"), patch.object(
			frappe.db, "get_value", return_value="Company B"
		):
			with self.assertRaises(frappe.PermissionError):
				security.enabled_workshop("Company A", "Workshop B")

	def test_disabled_workshop_does_not_block_historical_invoices(self):
		with patch.object(api, "require_customers", return_value=["Customer A"]), patch.object(
			frappe, "get_all", return_value=[{"name": "INV-001"}]
		) as get_all:
			self.assertEqual(api.get_my_invoices("Company A"), [{"name": "INV-001"}])
			self.assertEqual(get_all.call_args.kwargs["filters"]["company"], "Company A")

	def test_new_booking_checks_workshop_enablement(self):
		with patch.object(api, "require_customers", return_value=["Customer A"]), patch.object(
			api, "enabled_workshop", side_effect=frappe.PermissionError
		):
			with self.assertRaises(frappe.PermissionError):
				api.create_customer_booking(
					"Company A", "Customer A", "Workshop A", "Vehicle A", "2026-11-06"
				)

	def test_unverified_customer_has_no_access(self):
		with patch.object(security, "authorized_customers", return_value=set()):
			with self.assertRaises(frappe.PermissionError):
				security.require_customers("Company A")

	def test_unassigned_manager_cannot_edit_company(self):
		with patch.object(security, "_global_admin", return_value=False), patch.object(
			security, "_managed_companies", return_value={"Company A"}
		):
			self.assertFalse(security.can_manage_company("Company B", user="manager@example.invalid"))
			self.assertTrue(security.can_manage_company("Company A", user="manager@example.invalid"))

	def test_history_does_not_depend_on_workshop_booking_switch(self):
		with patch.object(api, "require_customers", return_value=["Customer A"]), patch.object(
			frappe, "get_all", return_value=[]
		) as get_all:
			api.get_my_job_cards("Company A")
			self.assertEqual(get_all.call_args.kwargs["filters"]["company"], "Company A")
			self.assertNotIn("booking_enabled", get_all.call_args.kwargs["filters"])
