"""Unit tests for the Phase 3 calendar API (requires the Frappe test runner)."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from servicems.api import calendar


class TestCalendarApi(TestCase):
    def test_rejects_invalid_date_ranges(self):
        with patch.object(frappe, "throw", side_effect=frappe.ValidationError):
            for start, end in [
                ("2026-11-06", "2026-11-05"),
                ("2026-01-01", "2027-01-02"),
                ("bad", "2026-11-05"),
                (["!=", "x"], "2026-11-05"),
            ]:
                with self.subTest(start=start), self.assertRaises(frappe.ValidationError):
                    calendar._date_range(start, end)

    def test_rejects_invalid_status(self):
        with patch.object(frappe, "throw", side_effect=frappe.ValidationError):
            with self.assertRaises(frappe.ValidationError):
                calendar.get_calendar_bookings("2026-11-05", "2026-11-06", status=["!=", ""])

    def test_rejects_invalid_booking_time(self):
        with patch.object(frappe, "throw", side_effect=frappe.ValidationError):
            for value in ("25:00", "09:90", ["!=", "x"]):
                with self.subTest(value=value), self.assertRaises(frappe.ValidationError):
                    calendar._time(value)

    @patch.object(calendar, "_enrich", return_value=[])
    @patch.object(calendar, "_bay_enabled", return_value=False)
    @patch.object(frappe, "get_list", return_value=[])
    def test_list_uses_permission_checked_get_list(self, get_list, bay_enabled, enrich):
        result = calendar.get_calendar_bookings("2026-11-05", "2026-11-06", workshop="Workshop")
        self.assertEqual(result["bookings"], [])
        self.assertFalse(result["bay_management_enabled"])
        self.assertEqual(get_list.call_args.kwargs["filters"]["workshop"], "Workshop")
        self.assertEqual(get_list.call_args.args[0], "Service Booking")

    @patch.object(frappe, "has_permission")
    @patch.object(frappe, "get_doc")
    @patch.object(calendar, "_validate_bay")
    def test_create_booking_does_not_override_status_or_owner(self, validate_bay, get_doc, has_permission):
        workshop = MagicMock()
        customer = MagicMock()
        vehicle = MagicMock(customer="Customer")
        created = MagicMock()
        created.insert.return_value = created
        created.as_dict.return_value = {"name": "SB-2026-1"}
        def docs(*args):
            value = args[0]
            if isinstance(value, dict):
                return created
            return {
                ("Service Workshop", "Workshop"): workshop,
                ("Customer", "Customer"): customer,
                ("Service Vehicle", "Vehicle"): vehicle,
            }[args]
        get_doc.side_effect = docs
        values = {
            "customer": "Customer",
            "service_vehicle": "Vehicle",
            "workshop": "Workshop",
            "booking_date": "2026-11-05",
            "booking_time": "09:00",
            "bay": "",
            "status": "Completed",
            "owner": "Administrator",
        }
        output = calendar.create_booking(values)
        self.assertEqual(output["name"], "SB-2026-1")
        payload = get_doc.call_args.args[0]
        self.assertNotIn("status", payload)
        self.assertNotIn("owner", payload)
        self.assertEqual(payload["booking_time"], "09:00")
        validate_bay.assert_called_once()

    @patch.object(frappe, "get_doc")
    def test_reschedule_requires_write_permission(self, get_doc):
        doc = get_doc.return_value
        doc.check_permission.side_effect = frappe.PermissionError()
        with self.assertRaises(frappe.PermissionError):
            calendar.reschedule_booking("SB-001", "2026-11-05", "10:00")
        doc.save.assert_not_called()

    @patch.object(frappe, "get_doc")
    def test_reschedule_non_pending_is_rejected(self, get_doc):
        get_doc.return_value.status = "Completed"
        with patch.object(frappe, "throw", side_effect=frappe.ValidationError):
            with self.assertRaises(frappe.ValidationError):
                calendar.reschedule_booking("SB-001", "2026-11-05", "10:00")
        get_doc.return_value.save.assert_not_called()
