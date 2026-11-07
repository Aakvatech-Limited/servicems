from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe
from werkzeug.wrappers import Request

from servicems import field_auth
from servicems.www import field


class TestFieldAuthentication(TestCase):
	def environment(self, user="technician@example.invalid", confirmed=False, referrer=None):
		return SimpleNamespace(
			session=frappe._dict(user=user, data=frappe._dict(servicems_field_login=confirmed)),
			request=Request.from_values(
				base_url="https://field.invalid", headers={"Referer": referrer or ""}
			),
			local=SimpleNamespace(flags=frappe._dict(), session_obj=Mock()),
			sessions=SimpleNamespace(get_csrf_token=lambda: "test-csrf"),
			Redirect=frappe.Redirect,
		)

	def test_guest_and_existing_desk_session_require_field_login(self):
		for user in ("Guest", "Administrator", "technician@example.invalid"):
			with self.subTest(user=user):
				environment = self.environment(user=user)
				with patch.object(field, "frappe", environment), self.assertRaises(frappe.Redirect):
					field.get_context(frappe._dict())
				self.assertEqual(environment.local.flags.redirect_location, field_auth.login_url())

	def test_successful_field_session_loads_account_and_csrf(self):
		environment = self.environment(confirmed=True)
		with patch.object(field, "frappe", environment):
			context = field.get_context(frappe._dict())
		self.assertEqual(context.field_user, environment.session.user)
		self.assertEqual(context.csrf_token, "test-csrf")
		self.assertEqual(context.no_cache, 1)

	def test_only_successful_login_from_field_marks_session(self):
		environment = self.environment(referrer="https://field.invalid/field-login?redirect-to=%2Ffield")
		with patch.object(field_auth, "frappe", environment):
			field_auth.record_field_login(Mock())
		self.assertTrue(environment.session.data.servicems_field_login)
		environment.local.session_obj.update.assert_called_once_with(force=True)

	def test_guest_other_origin_and_normal_desk_login_do_not_mark_session(self):
		for user, referrer in (
			("Guest", "https://field.invalid/field-login"),
			("Administrator", "https://other.invalid/field-login"),
			("Administrator", "https://field.invalid/login"),
			("Administrator", "https://field.invalid/field?field_login=1"),
		):
			with self.subTest(user=user, referrer=referrer):
				environment = self.environment(user=user, referrer=referrer)
				with patch.object(field_auth, "frappe", environment):
					field_auth.record_field_login(Mock())
				self.assertFalse(environment.session.data.servicems_field_login)
				environment.local.session_obj.update.assert_not_called()

	def test_native_login_options_restore_existing_user_even_on_error(self):
		for exception in (None, RuntimeError("context failure")):
			environment = self.environment()

			def native_context(context, environment=environment, exception=exception):
				self.assertEqual(environment.session.user, "Guest")
				if exception:
					raise exception
				return context

			with (
				patch.object(field_auth, "frappe", environment),
				patch("frappe.www.login.get_context", native_context),
			):
				if exception:
					with self.assertRaises(RuntimeError):
						field_auth.login_context({})
				else:
					field_auth.login_context({})
			self.assertEqual(environment.session.user, "technician@example.invalid")
