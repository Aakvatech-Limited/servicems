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
		for doctype in ("Service Booking", "Service Workshop"):
			frappe.clear_cache(doctype=doctype)
		if getattr(self, "restricted_user", None):
			frappe.clear_cache()
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
		if getattr(self, "created", None):
			return calendar.create_booking(
				{
					"customer": self.created["customer"],
					"service_vehicle": self.created["service_vehicle"],
					**booking,
				}
			)
		self.created = calendar.create_booking(booking, self.customer, self.vehicle)
		return self.created

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

	def test_untimed_bookings_without_bays_remain_supported(self):
		for enabled in (False, True):
			self.set_bays(enabled)
			doc = self.create(booking_time="")
			calendar.reschedule_booking(doc["name"], str(frappe.utils.add_days(self.day, 1)))
			self.assertFalse(frappe.db.get_value("Service Booking", doc["name"], "booking_time"))

	def test_bay_creation_and_rescheduling_require_a_start_time(self):
		self.set_bays(True)
		bay = self.bay()
		with self.assertRaisesRegex(frappe.ValidationError, "start time is required"):
			self.create(bay=bay, booking_time="")
		self.assertEqual(frappe.db.count("Service Booking", {"bay": bay}), 0)
		doc = self.create(bay=bay)
		with self.assertRaisesRegex(frappe.ValidationError, "start time is required"):
			calendar.reschedule_booking(doc["name"], str(frappe.utils.add_days(self.day, 1)))
		self.assertEqual(str(frappe.db.get_value("Service Booking", doc["name"], "booking_date")), self.day)

	def test_native_document_cannot_bypass_bay_time_or_duplicate_validation(self):
		self.set_bays(True)
		bay = self.bay()
		original = self.create(bay=bay)
		for time in ("", "09:05"):
			values = {**original, "name": None, "booking_time": time}
			with self.subTest(time=time), self.assertRaises(frappe.ValidationError):
				frappe.get_doc(values).insert()
		# Midnight is a real start time, not an empty timedelta.
		midnight = frappe.get_doc({**original, "name": None, "booking_time": "00:00:00"}).insert()
		self.assertIsNotNone(midnight.booking_time)

	def test_historical_untimed_bay_allocation_can_be_edited_but_not_rescheduled(self):
		self.set_bays(True)
		bay = self.bay()
		doc = self.create(bay=bay)
		frappe.db.set_value("Service Booking", doc["name"], "booking_time", None)
		legacy = frappe.get_doc("Service Booking", doc["name"])
		legacy.service_description = "Unchanged historical allocation"
		legacy.save()
		legacy.booking_date = frappe.utils.add_days(self.day, 1)
		with self.assertRaisesRegex(frappe.ValidationError, "start time is required"):
			legacy.save()
		self.set_bays(False)
		calendar.reschedule_booking(doc["name"], str(frappe.utils.add_days(self.day, 1)))
		self.assertEqual(frappe.db.get_value("Service Booking", doc["name"], "bay"), bay)

	def restricted_reader(self, workshop_access=False, own_only=True):
		from frappe.permissions import add_permission

		role = "Calendar Reader " + self.suffix
		frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()
		self.restricted_user = "calendar-" + self.suffix.lower() + "@example.invalid"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": self.restricted_user,
				"first_name": "Calendar Reader",
				"user_type": "System User",
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert()
		permission = add_permission("Service Booking", role)
		frappe.db.set_value("Custom DocPerm", permission, "if_owner", int(own_only))
		# Installed dependency hooks grant linked-doctype select access automatically.
		# Remove only this temporary role's grants to reproduce a true restricted reader.
		for doctype in ("Service Workshop", "Bay", "Customer", "Service Vehicle"):
			frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": role})
			frappe.clear_cache(doctype=doctype)
		frappe.clear_cache(doctype="Service Booking")
		if workshop_access:
			add_permission("Service Workshop", role)
		return self.restricted_user

	def test_restricted_reader_loads_owned_bookings_without_linked_doctype_access(self):
		self.set_bays(True)
		visible = self.create()
		hidden = self.create()
		user = self.restricted_reader()
		frappe.db.set_value("Service Booking", visible["name"], "owner", user)
		frappe.set_user(user)
		self.assertFalse(frappe.has_permission("Service Workshop", "read"))
		self.assertFalse(frappe.has_permission("Bay", "read"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Service Workshop", fields=["name"], page_length=500)
		for enabled in (True, False):
			frappe.set_user("Administrator")
			self.set_bays(enabled)
			frappe.set_user(user)
			result = calendar.get_calendar_bookings(self.day, self.day)
			self.assertIn(visible["name"], [row["name"] for row in result["bookings"]])
			self.assertNotIn(hidden["name"], [row["name"] for row in result["bookings"]])
			self.assertEqual(result["bays"], [])
			self.assertEqual(calendar.get_calendar_workshops(), [])
			self.assertEqual(
				[
					row["name"]
					for row in calendar.get_calendar_bookings(self.day, self.day, workshop=self.workshop)[
						"bookings"
					]
				],
				[visible["name"]],
			)

	def test_workshop_options_paginate_and_apply_user_permissions(self):
		from frappe.permissions import add_user_permission

		base = frappe.get_doc("Service Workshop", self.workshop)
		names = [f"Calendar Paging {self.suffix} {index:04d}" for index in range(501)]
		frappe.db.bulk_insert(
			"Service Workshop",
			fields=["name", "workshop_name", "company", "parts_warehouse", "workshop_warehouse"],
			values=[
				(name, name, base.company, base.parts_warehouse, base.workshop_warehouse) for name in names
			],
		)
		first = calendar.get_calendar_workshops()
		second = calendar.get_calendar_workshops(start=500)
		self.assertNotIn(names[-1], [row.name for row in first])
		self.assertIn(names[-1], [row.name for row in second])
		user = self.restricted_reader(workshop_access=True, own_only=False)
		self.set_bays(False)
		visible = self.create(workshop=names[-1])
		self.create()
		add_user_permission("Service Workshop", names[-1], user)
		frappe.set_user(user)
		self.assertEqual([row.name for row in calendar.get_calendar_workshops()], [names[-1]])
		self.assertEqual(calendar.get_calendar_workshops(start=500), [])
		self.assertEqual(
			[row["name"] for row in calendar.get_calendar_bookings(self.day, self.day)["bookings"]],
			[visible["name"]],
		)
		self.assertEqual(
			calendar.get_calendar_bookings(self.day, self.day, workshop=self.workshop)["bookings"], []
		)

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

	def test_native_lookup_reaches_customer_and_vehicle_beyond_first_500(self):
		from frappe.desk.search import search_link

		prefix = "Calendar Paging " + self.suffix
		customers = []
		for index in range(501):
			values = {**self.customer, "customer_name": f"{prefix} {index:04d}"}
			customers.append(frappe.get_doc({"doctype": "Customer", **values}).insert().name)
		first_page = frappe.get_list(
			"Customer",
			filters={"customer_name": ["like", prefix + "%"]},
			fields=["name"],
			order_by="modified desc",
			limit=500,
		)
		self.assertNotIn(customers[0], [row.name for row in first_page])
		self.assertIn(
			customers[0], [row["value"] for row in search_link("Customer", customers[0], page_length=20)]
		)
		vehicles = []
		for index in range(501):
			vehicles.append(
				frappe.get_doc(
					{
						"doctype": "Service Vehicle",
						"registration_number": f"CP-{self.suffix}-{index:04d}",
						"customer": customers[0],
						"vehicle_model": self.model,
					}
				)
				.insert()
				.name
			)
		first_page = frappe.get_list(
			"Service Vehicle",
			filters={"customer": customers[0]},
			fields=["name"],
			order_by="modified desc",
			limit=500,
		)
		self.assertNotIn(vehicles[0], [row.name for row in first_page])
		self.assertIn(
			vehicles[0],
			[
				row["value"]
				for row in search_link(
					"Service Vehicle", vehicles[0], filters={"customer": customers[0]}, page_length=20
				)
			],
		)
