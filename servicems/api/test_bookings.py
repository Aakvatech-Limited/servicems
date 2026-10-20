"""Unit tests; no site records are created or changed."""

from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from servicems.api import bookings


class TestBookingCalendar(TestCase):
	def setUp(self):
		flags = patch.object(frappe.local, "flags", frappe._dict(in_test=False), create=True)
		flags.start()
		self.addCleanup(flags.stop)
		self.translation = patch.object(bookings, "_", side_effect=lambda text: text)
		self.translation.start()
		self.addCleanup(self.translation.stop)
		self.throw = patch.object(frappe, "throw", side_effect=_raise_validation)
		self.throw.start()
		self.addCleanup(self.throw.stop)

	def test_date_boundaries(self):
		self.assertEqual(
			bookings._date_range("2026-01-01", "2026-02-01"), (date(2026, 1, 1), date(2026, 2, 1))
		)
		for start, end in [
			("2026-02-01", "2026-01-01"),
			("2026-01-01", "2027-01-02"),
			(None, None),
			(["!=", ""], "2026-01-01"),
		]:
			with self.subTest(start=start), self.assertRaises(frappe.ValidationError):
				bookings._date_range(start, end)

	@patch.object(frappe, "get_list")
	def test_returns_individual_permission_filtered_bookings(self, get_list):
		rows = [{"name": "one"}, {"name": "two"}]
		get_list.return_value = rows
		self.assertEqual(
			bookings.get_calendar_bookings("2026-01-01", "2026-01-02", "Workshop", "Vehicle"), rows
		)
		kwargs = get_list.call_args.kwargs
		self.assertEqual(kwargs["filters"]["workshop"], "Workshop")
		self.assertEqual(kwargs["filters"]["service_vehicle"], "Vehicle")
		self.assertNotIn("group_by", kwargs)
		self.assertNotIn("ignore_permissions", kwargs)

	@patch.object(frappe, "get_list", side_effect=frappe.PermissionError)
	def test_does_not_bypass_read_permission(self, get_list):
		with self.assertRaises(frappe.PermissionError):
			bookings.get_calendar_bookings("2026-01-01", "2026-01-02")

	@patch.object(frappe, "get_list", return_value=[{}] * 10001)
	def test_does_not_silently_drop_bookings(self, get_list):
		with self.assertRaises(frappe.ValidationError):
			bookings.get_calendar_bookings("2026-01-01", "2026-01-02")

	def test_rejects_filter_operator_injection(self):
		with self.assertRaises(frappe.ValidationError):
			bookings.get_calendar_bookings("2026-01-01", "2026-01-02", workshop=["!=", ""])
		with self.assertRaises(frappe.ValidationError):
			bookings._document_values({"customer": ["!=", ""]}, ("customer",))

	@patch.object(frappe, "has_permission")
	@patch.object(frappe, "get_doc")
	def test_booking_accepts_no_bay_or_time_and_limits_writable_fields(self, get_doc, has_permission):
		vehicle = MagicMock(customer="Customer")
		created = MagicMock()
		created.insert.return_value = created
		created.as_dict.return_value = {"name": "booking"}
		get_doc.side_effect = lambda *args: created if isinstance(args[0], dict) else vehicle
		result = bookings.create_booking(
			{
				"customer": "Customer",
				"service_vehicle": "Vehicle",
				"booking_date": "2026-01-01",
				"workshop": "Workshop",
				"status": "Completed",
				"owner": "Administrator",
			}
		)
		self.assertEqual(result["name"], "booking")
		payload = get_doc.call_args.args[0]
		for field in ("owner", "status"):
			self.assertNotIn(field, payload)
		self.assertEqual(payload["bay"], "")
		self.assertEqual(payload["booking_time"], "")
		has_permission.assert_called_once_with("Service Booking", "create", throw=True)
		created.insert.assert_called_once_with()

	@patch.object(frappe, "has_permission")
	@patch.object(frappe, "get_doc")
	def test_rejects_another_customers_vehicle(self, get_doc, has_permission):
		get_doc.return_value = MagicMock(customer="Another Customer")
		with self.assertRaises(frappe.ValidationError):
			bookings.create_booking(
				{
					"customer": "Customer",
					"service_vehicle": "Vehicle",
					"booking_date": "2026-01-01",
					"workshop": "Workshop",
				}
			)
		get_doc.return_value.insert.assert_not_called()

	@patch.object(frappe, "has_permission", side_effect=frappe.PermissionError)
	@patch.object(frappe, "get_doc")
	def test_checks_permission_before_creating_related_records(self, get_doc, has_permission):
		with self.assertRaises(frappe.PermissionError):
			bookings.create_booking(
				{"booking_date": "2026-01-01", "workshop": "Workshop"}, new_customer={"customer_name": "Name"}
			)
		get_doc.assert_not_called()


def _raise_validation(message):
	raise frappe.ValidationError(message)
