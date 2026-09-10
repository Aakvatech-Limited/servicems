import frappe
from frappe.tests import IntegrationTestCase

from servicems.tests.utils import create_test_data


class ServiceMSTestCase(IntegrationTestCase):
	"""Loads the shared fixtures once per class and rolls back each test's changes."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		create_test_data()

	def tearDown(self):
		frappe.db.rollback()
		super().tearDown()
