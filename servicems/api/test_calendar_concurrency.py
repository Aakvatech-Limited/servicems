"""Independent committed requests against a dedicated, temporary test Bay."""

import multiprocessing
import time
from pathlib import Path
from unittest import TestCase

import frappe

from servicems.api import calendar


class TestCalendarConcurrency(TestCase):
	def setUp(self):
		self.previous_user = frappe.session.user
		frappe.set_user("Administrator")
		self.previous_enabled = calendar._bay_enabled()
		self.workshop = frappe.get_all("Service Workshop", pluck="name", limit=1)[0]
		vehicle = frappe.get_all("Service Vehicle", fields=["name", "customer"], limit=1)[0]
		self.bay = "Calendar Concurrent " + frappe.generate_hash(length=10)
		self.booking = {
			"customer": vehicle.customer,
			"service_vehicle": vehicle.name,
			"workshop": self.workshop,
			"bay": self.bay,
			"booking_date": str(frappe.utils.add_days(frappe.utils.today(), 3000)),
			"booking_time": "14:25:32",
		}
		frappe.db.set_single_value("Service Settings", "enable_bay_management", 1)
		frappe.get_doc({"doctype": "Bay", "bay": self.bay, "service_workshop": self.workshop}).insert()
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for name in frappe.get_all("Service Booking", filters={"bay": self.bay}, pluck="name"):
			frappe.delete_doc("Service Booking", name)
		frappe.delete_doc("Bay", self.bay)
		frappe.db.set_single_value("Service Settings", "enable_bay_management", self.previous_enabled)
		frappe.db.commit()
		frappe.clear_document_cache("Service Settings", "Service Settings")
		frappe.set_user(self.previous_user)

	def requests(self, requests):
		context = multiprocessing.get_context("spawn")
		go = context.Event()
		pipes = [context.Pipe(duplex=False) for request in requests]
		workers = [
			context.Process(
				target=run_request,
				args=(frappe.local.site, str(Path(frappe.local.sites_path).resolve()), request, go, pipe[1]),
			)
			for request, pipe in zip(requests, pipes, strict=True)
		]
		try:
			for worker in workers:
				worker.start()
			connections = []
			for pipe, _ in pipes:
				self.assertTrue(pipe.poll(20), "Request failed to connect")
				connections.append(pipe.recv()["connection"])
			self.assertEqual(len(set(connections)), 2)
			go.set()
			results = []
			for worker, (pipe, _) in zip(workers, pipes, strict=True):
				self.assertTrue(pipe.poll(40), "Request failed to finish")
				results.append(pipe.recv())
				worker.join(timeout=5)
				self.assertEqual(worker.exitcode, 0, results[-1])
			frappe.db.rollback()
			return results
		finally:
			for worker in workers:
				if worker.is_alive():
					worker.terminate()
				worker.join(timeout=5)
			for pipe in pipes:
				for endpoint in pipe:
					endpoint.close()

	def test_concurrent_same_start_creates_only_one_booking(self):
		results = self.requests([{"booking": self.booking}] * 2)
		self.assertEqual(sorted(result["result"] for result in results), ["rejected", "saved"])
		self.assertEqual(frappe.db.count("Service Booking", {"bay": self.bay}), 1)

	def test_concurrent_missing_start_creates_no_allocations(self):
		results = self.requests([{"booking": {**self.booking, "booking_time": ""}}] * 2)
		self.assertTrue(all(result["result"] == "rejected" for result in results))
		self.assertTrue(all("start time is required" in result["reason"] for result in results))
		self.assertEqual(frappe.db.count("Service Booking", {"bay": self.bay}), 0)

	def test_concurrent_reschedules_cannot_allocate_the_same_start(self):
		names = [
			calendar.create_booking(
				{
					**self.booking,
					"booking_date": str(frappe.utils.add_days(self.booking["booking_date"], offset)),
				}
			)["name"]
			for offset in (1, 2)
		]
		frappe.db.commit()
		results = self.requests(
			[
				{
					"name": name,
					"booking_date": self.booking["booking_date"],
					"booking_time": self.booking["booking_time"],
				}
				for name in names
			]
		)
		self.assertEqual(sorted(result["result"] for result in results), ["rejected", "saved"])
		self.assertEqual(
			frappe.db.count(
				"Service Booking", {"bay": self.bay, "booking_date": self.booking["booking_date"]}
			),
			1,
		)


def run_request(site, sites_path, request, go, pipe):
	frappe.init(site=site, sites_path=sites_path)
	frappe.connect()
	frappe.set_user("Administrator")
	try:
		pipe.send({"connection": frappe.db.sql("SELECT CONNECTION_ID()")[0][0]})
		if not go.wait(timeout=25):
			raise TimeoutError("Concurrent request did not start")
		try:
			if "booking" in request:
				calendar.create_booking(request["booking"])
			else:
				calendar.reschedule_booking(**request)
			time.sleep(0.3)
			frappe.db.commit()
			pipe.send({"result": "saved"})
		except frappe.ValidationError as error:
			frappe.db.rollback()
			pipe.send({"result": "rejected", "reason": str(error)})
		except Exception as error:
			frappe.db.rollback()
			pipe.send({"result": "error", "reason": repr(error)})
	finally:
		pipe.close()
		frappe.destroy()
