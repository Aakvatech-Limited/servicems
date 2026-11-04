"""Calendar actions against real Frappe records, rolled back after each test."""

from unittest import TestCase

import frappe

from servicems.api import calendar


class TestCalendarRecords(TestCase):
	def setUp(self):
		self.previous_user = frappe.session.user
		frappe.set_user("Administrator")
		frappe.db.savepoint("calendar_records")
		self.suffix = frappe.generate_hash(length=8).upper()
		self.workshop = frappe.get_all("Service Workshop", pluck="name", limit=1)[0]
		self.model = frappe.get_all("Vehicle Model", pluck="name", limit=1)[0]
		self.day = frappe.utils.today()
		self.customer = {
			"customer_name": "Calendar UAT " + self.suffix,
			"customer_type": "Individual",
			"customer_group": frappe.get_all(
				"Customer Group", filters={"is_group": 0}, pluck="name", limit=1
			)[0],
			"territory": frappe.get_all("Territory", filters={"is_group": 0}, pluck="name", limit=1)[0],
		}
		for field in calendar._customer_required_fields():
			self.customer[field["fieldname"]] = (
				"6- Other"
				if field["fieldtype"] == "Select" and "6- Other" in field["options"]
				else "999999999"
			)
		self.vehicle = {"registration_number": "CAL-" + self.suffix, "vehicle_model": self.model}

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="calendar_records")
		frappe.db.value_cache.clear()
		frappe.clear_document_cache("Service Settings", "Service Settings")
		frappe.set_user(self.previous_user)

	def set_bays(self, enabled):
		frappe.db.set_single_value("Service Settings", "enable_bay_management", enabled)
		frappe.db.value_cache.clear()

	def bay(self):
		return (
			frappe.get_doc(
				{"doctype": "Bay", "bay": "Calendar UAT " + self.suffix, "service_workshop": self.workshop}
			)
			.insert()
			.name
		)

	def create(self, **values):
		booking = {"booking_date": self.day, "booking_time": "09:05", "workshop": self.workshop, **values}
		return calendar.create_booking(booking, self.customer, self.vehicle)

	def test_creates_real_customer_vehicle_and_booking(self):
		self.set_bays(False)
		doc = self.create()
		self.assertTrue(frappe.db.exists("Service Booking", doc["name"]))
		self.assertEqual(
			frappe.db.get_value("Customer", doc["customer"], "customer_name"), self.customer["customer_name"]
		)
		self.assertEqual(
			frappe.db.get_value("Service Vehicle", doc["service_vehicle"], "customer"), doc["customer"]
		)
		self.assertEqual(doc["status"], "Pending")
		self.assertFalse(doc.get("bay"))

	def test_pending_booking_reschedules_real_record(self):
		self.set_bays(False)
		doc = self.create()
		day = str(frappe.utils.add_days(self.day, 1))
		calendar.reschedule_booking(doc["name"], day, "10:15")
		updated = frappe.get_doc("Service Booking", doc["name"])
		self.assertEqual(str(updated.booking_date), day)
		self.assertEqual(str(updated.booking_time), "10:15:00")

	def test_same_start_conflict_is_rejected(self):
		self.set_bays(True)
		bay = self.bay()
		doc = self.create(bay=bay)
		with self.assertRaises(frappe.ValidationError):
			calendar.create_booking(
				{
					"customer": doc["customer"],
					"service_vehicle": doc["service_vehicle"],
					"booking_date": self.day,
					"booking_time": "09:05",
					"workshop": self.workshop,
					"bay": bay,
				}
			)
		self.assertEqual(frappe.db.count("Service Booking", {"bay": bay}), 1)

	def test_different_start_is_not_treated_as_time_range_overlap(self):
		self.set_bays(True)
		bay = self.bay()
		doc = self.create(bay=bay)
		second = calendar.create_booking(
			{
				"customer": doc["customer"],
				"service_vehicle": doc["service_vehicle"],
				"booking_date": self.day,
				"booking_time": "09:06",
				"workshop": self.workshop,
				"bay": bay,
			}
		)
		self.assertNotEqual(doc["name"], second["name"])

	def test_disabled_bay_preserves_historical_allocation_on_reschedule(self):
		self.set_bays(True)
		bay = self.bay()
		doc = self.create(bay=bay)
		self.set_bays(False)
		calendar.reschedule_booking(doc["name"], self.day, "11:00")
		self.assertEqual(frappe.db.get_value("Service Booking", doc["name"], "bay"), bay)

	def test_vehicle_must_belong_to_customer(self):
		self.set_bays(False)
		doc = self.create()
		other = frappe.get_all("Customer", filters={"name": ["!=", doc["customer"]]}, pluck="name", limit=1)[
			0
		]
		with self.assertRaises(frappe.ValidationError):
			calendar.create_booking(
				{
					"customer": other,
					"service_vehicle": doc["service_vehicle"],
					"booking_date": self.day,
					"workshop": self.workshop,
				}
			)

	def test_filters_and_timezone_use_real_records(self):
		self.set_bays(False)
		doc = self.create()
		result = calendar.get_calendar_bookings(
			self.day,
			self.day,
			customer=doc["customer"],
			vehicle=doc["service_vehicle"],
			workshop=self.workshop,
			status="Pending",
		)
		self.assertEqual([row["name"] for row in result["bookings"]], [doc["name"]])
		self.assertEqual(result["timezone"], frappe.utils.get_system_timezone())

	def test_guest_cannot_create_bookings(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			calendar.create_booking(
				{
					"customer": "blocked",
					"service_vehicle": "blocked",
					"booking_date": self.day,
					"workshop": self.workshop,
				}
			)

	def test_native_calendar_link_sync_preserves_other_items_and_collapse(self):
		from servicems.navigation import _navigation_write

		doc = frappe.get_doc("Sidebar", "Service Management")
		other = [row.as_dict() for row in doc.items if row.label != "Booking Calendar"]
		entry = next(row for row in doc.items if row.label == "Booking Calendar")
		entry.link_type = "URL"
		entry.url = "/bookings"
		entry.link_to = ""
		with _navigation_write():
			doc.save(ignore_permissions=True)
		calendar.sync_calendar_navigation()
		updated = frappe.get_doc("Sidebar", "Service Management")
		entry = next(row for row in updated.items if row.label == "Booking Calendar")
		self.assertEqual((entry.link_type, entry.link_to), ("Page", "service-booking-calendar"))

		# Parent modified timestamps change on save; navigation row values must not.
		def values(rows):
			return [{k: v for k, v in row.items() if k not in ("modified", "modified_by")} for row in rows]

		self.assertEqual(
			values(other), values([row.as_dict() for row in updated.items if row.label != "Booking Calendar"])
		)
		self.assertFalse(calendar.sync_calendar_navigation()["Sidebar"])
