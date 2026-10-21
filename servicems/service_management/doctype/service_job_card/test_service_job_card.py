# Copyright (c) 2026, Aakvatech Limited
import unittest
from unittest.mock import patch

import frappe
from servicems.service_management.doctype.service_job_card.service_job_card import ServiceJobCard


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
