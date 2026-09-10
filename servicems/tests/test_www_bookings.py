import frappe
from frappe.utils import set_request

from servicems.tests.base import ServiceMSTestCase
from servicems.www import bookings


class TestBookingsPage(ServiceMSTestCase):
	def test_boot(self):
		boot = bookings.get_boot()
		self.assertEqual(boot.default_route, "/bookings")
		self.assertEqual(boot.site_name, frappe.local.site)
		self.assertEqual(boot.frappe_version, frappe.__version__)
		self.assertTrue(boot.csrf_token)

	def test_context_for_logged_in_user(self):
		set_request(path="/bookings")
		context = bookings.get_context()
		self.assertEqual(context.default_route, "/bookings")
		self.assertTrue(context.csrf_token)

	def test_context_for_guest(self):
		set_request(path="/bookings")
		frappe.set_user("Guest")  # nosemgrep
		try:
			self.assertTrue(bookings.get_context().csrf_token)
		finally:
			frappe.set_user("Administrator")  # nosemgrep

	def test_route_rule_serves_nested_paths(self):
		rules = frappe.get_hooks("website_route_rules", app_name="servicems")
		self.assertEqual(rules[0]["to_route"], "bookings")
		self.assertTrue(rules[0]["from_route"].startswith("/bookings/"))

	def test_page_is_not_cached(self):
		"""The page embeds the session CSRF token, so a cached copy breaks every POST from the booking app."""
		self.assertEqual(bookings.no_cache, 1)
		self.assertFalse(getattr(bookings, "cache", None))
