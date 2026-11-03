# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, now, nowdate, nowtime, time_diff_in_hours
from frappe.website.website_generator import WebsiteGenerator


def get_service_transaction_company(fallback_company=None):
	company = frappe.db.get_single_value("Service Settings", "company")
	return company or fallback_company


def reconcile_parts_quantities(issued, consumed=0, returned=0):
	"""Validate one Job Card allocation in stock UOM; no ledger mutations."""
	quantities = [flt(value, 6) for value in (issued, consumed, returned)]
	if any(not math.isfinite(value) or value < 0 for value in quantities):
		frappe.throw(_("Parts quantities cannot be negative."))
	issued_qty, consumed_qty, returned_qty = quantities
	if consumed_qty + returned_qty > issued_qty + 0.0000005:
		frappe.throw(_("Consumed and returned quantity exceeds quantity issued."))
	outstanding = flt(issued_qty - consumed_qty - returned_qty, 6)
	return {
		"issued": issued_qty,
		"consumed": consumed_qty,
		"returned": returned_qty,
		"outstanding": max(outstanding, 0),
	}


class ServiceJobCard(WebsiteGenerator):
	def after_insert(self):
		if self.service_booking:
			frappe.db.set_value(
				"Service Booking",
				self.service_booking,
				{
					"status": "In Progress",
					"job_card": self.name,
				},
			)

	def validate(self):
		self.set_company_from_service_settings()
		self.update_tables()
		self.set_parts_rate()
		self.set_totals()
		self.vaildate_complete()
		self.validate_quality_check()
		self.validate_bay_management()
		self.validate_labour_entries()
		from servicems.costing import validate_costing

		validate_costing(self)

	def validate_labour_entries(self):
		for row in self.labour_entries:
			if row.stopped_at and get_datetime(row.stopped_at) <= get_datetime(row.started_at):
				frappe.throw(_("Labour end must be after start on row {0}").format(row.idx))
			row.hours = flt(time_diff_in_hours(row.stopped_at, row.started_at), 3) if row.stopped_at else 0
			if self.status in ("Completed", "Closed") and not row.stopped_at:
				frappe.throw(_("Stop all running labour entries before completion"))
			for other in self.labour_entries:
				if other is row or row.technician != other.technician:
					continue
				if get_datetime(row.started_at) < get_datetime(other.stopped_at or now()) and get_datetime(
					other.started_at
				) < get_datetime(row.stopped_at or now()):
					frappe.throw(_("Overlapping labour entries for {0}").format(row.technician))

	@frappe.whitelist()
	def start_labour(self, technician, task=None):
		self.check_permission("write")
		if self.docstatus != 0:
			frappe.throw(_("Cannot start labour on a submitted Job Card"))
		frappe.db.sql("select name from `tabEmployee` where name=%s for update", technician)
		if not frappe.db.exists("Employee", technician):
			frappe.throw(_("Select a valid Employee"))
		active = frappe.get_all(
			"Service Labour Entry",
			filters={"technician": technician, "stopped_at": ["is", "not set"]},
			fields=["name"],
			limit_page_length=1,
		)
		if active:
			frappe.throw(_("Technician already has an active labour entry"))
		self.append("labour_entries", {"technician": technician, "task": task, "started_at": now()})
		self.save()
		return self.name

	@frappe.whitelist()
	def stop_labour(self, technician):
		self.check_permission("write")
		if self.docstatus != 0:
			frappe.throw(_("Cannot stop labour on a submitted Job Card"))
		active = [row for row in self.labour_entries if row.technician == technician and not row.stopped_at]
		if len(active) != 1:
			frappe.throw(_("Expected one running labour entry for this technician"))
		active[0].stopped_at = now()
		self.save()
		return active[0].hours

	def validate_bay_management(self):
		if self.bay and not frappe.db.get_single_value("Service Settings", "enable_bay_management"):
			previous_bay = (
				None if self.is_new() else frappe.db.get_value("Service Job Card", self.name, "bay")
			)
			if self.bay != previous_bay:
				frappe.throw(_("Enable Bay Management in Service Settings before allocating a bay."))

	def validate_quality_check(self):
		"""Keep historical completed cards intact; enforce QC for new transitions."""
		was_confirmed = False
		if not self.is_new():
			previous = self.get_doc_before_save()
			was_confirmed = bool(previous and previous.quality_check_confirmed)

		if self.quality_check_confirmed and not was_confirmed:
			self.quality_checked_by = frappe.session.user
			self.quality_checked_on = now()
		elif not self.quality_check_confirmed:
			self.quality_checked_by = None
			self.quality_checked_on = None

		if self.status != "Completed" or not frappe.db.get_single_value(
			"Service Settings", "require_final_quality_check"
		):
			return

		if not self.is_new():
			previous = self.get_doc_before_save()
			if previous and previous.status in ("Completed", "Closed"):
				return
		if not self.quality_check_confirmed:
			frappe.throw(_("Final quality check must be confirmed before completion."))

	def set_company_from_service_settings(self):
		service_company = frappe.db.get_single_value("Service Settings", "company")
		default_company = frappe.defaults.get_global_default("company")
		self.company = self.company or service_company or default_company

	def before_submit(self):
		from servicems.parts import allocations

		buckets = allocations(self)
		issued_plans = {bucket["row"].service_part_row for bucket in buckets.values()}
		if any(
			row.qty
			and not row.customer_supplied
			and not row.use_existing_spares
			and row.name not in issued_plans
			for row in self.parts
		):
			frappe.throw(
				_(
					"Issue all planned owned parts, or remove unused planned rows, before closing the Job Card."
				)
			)
		if any(bucket["outstanding"] for bucket in buckets.values()):
			frappe.throw(_("Consume or return all outstanding workshop parts before closing the Job Card."))
		if not self.internal_maintenance:
			from servicems.billing import validate_closure

			validate_closure(self)

	def on_submit(self):
		if self.status != "Completed":
			frappe.throw(_("It is not allowed to submit if it is not completed"))

		if self.service_booking:
			frappe.db.set_value("Service Booking", self.service_booking, "status", "Completed")

	def update_tables(self):
		# nosemgrep: frappe-semgrep-rules.rules.frappe-modifying-child-tables-while-iterating
		for template in self.services:  # appends to tasks/parts, not to services
			if template.bypass_billable and template.applied:
				continue

			service_template = frappe.get_doc("Service Template", template.service)

			if not template.bypass_billable:
				template.is_billable = service_template.is_billable

			if not template.applied:
				if service_template.tasks:
					for task in service_template.tasks:
						self.append(
							"tasks",
							{
								"task_name": task.task_name,
								"template": service_template.name,
							},
						)

				if service_template.parts:
					for part in service_template.parts:
						self.append(
							"parts",
							{
								"item": part.item,
								"qty": part.qty,
								"rate": get_item_price(
									part.item,
									self.get_price_list(service_template.price_list),
									self.company,
								),
								"is_billable": part.is_billable,
							},
						)

				template.applied = 1

	def set_totals(self):
		self.service_charges = 0
		self.spares_cost = 0
		self.total = 0

		if self.services:
			for service in self.services:
				if not service.rate or service.rate == 0:
					service.rate = get_item_price(
						service.item, self.get_price_list(service.price_list), self.company
					)
				if service.is_billable:
					self.service_charges += service.rate
		if self.parts:
			for part in self.parts:
				if part.is_billable:
					self.spares_cost += part.rate * part.qty
		if self.supplied_parts:
			for supplied_part in self.supplied_parts:
				if supplied_part.is_billable:
					self.spares_cost += supplied_part.rate * supplied_part.qty

		self.total = self.service_charges + self.spares_cost

	def set_parts_rate(self):
		price_list = self.get_price_list()
		for item in self.parts:
			if item.rate:
				continue

			item.rate = get_item_price(item.item, price_list, self.company)

	@frappe.whitelist()
	def create_parts_entry(self, type):
		self.check_permission("write")
		if not self.parts:
			frappe.throw(_("Add Parts and Consumable Supplied first."))

		supplied_items = []
		items = []
		for item_row in self.parts:
			if item_row.service_parts_entry or item_row.use_existing_spares or not item_row.qty:
				continue

			item_dict = frappe._dict(
				{
					"item_code": item_row.item,
					"qty": item_row.qty,
					"basic_rate": item_row.rate,
				}
			)

			items.append(item_dict)
			supplied_items.append(item_row.name)

		if not len(items):
			frappe.throw(_("Items not available to create Parts Entry."))

		service_parts_entry = frappe.get_doc(
			dict(
				doctype="Service Parts Entry",
				posting_date=nowdate(),
				posting_time=nowtime(),
				company=self.company,
				service_job_card=self.name,
				items=items,
			),
		)

		service_parts_entry.insert()
		service_parts_entry.submit()

		if not service_parts_entry.get("name"):
			return

		frappe.msgprint(
			_("Service Parts Entry {0} Created").format(service_parts_entry.name),
			alert=True,
		)

		self.update_supplied_parts_details(supplied_items, service_parts_entry.name)

		if type == "call":
			self.save()

	def update_supplied_parts_details(self, supplied_items, parts_entry_no):
		# nosemgrep: frappe-semgrep-rules.rules.frappe-modifying-child-tables-while-iterating
		for row in self.parts:  # appends to supplied_parts, not to parts
			if row.name not in supplied_items:
				continue

			row.service_parts_entry = parts_entry_no

			self.append(
				"supplied_parts",
				{
					"item": row.item,
					"qty": row.qty,
					"rate": row.rate,
					"is_billable": row.is_billable,
				},
			)

	def validate_stock_transfer_configuration(self, workshop, transaction_company):
		"""Fail before creating a Stock Entry with incompatible workshop warehouses."""
		if not transaction_company:
			frappe.throw(_("Set a company before issuing workshop parts."))
		if not workshop.parts_warehouse or not workshop.workshop_warehouse:
			frappe.throw(_("Set both Parts Warehouse and Workshop Warehouse on the Service Workshop."))
		if workshop.parts_warehouse == workshop.workshop_warehouse:
			frappe.throw(_("Parts Warehouse and Workshop Warehouse must be different."))
		for warehouse in (workshop.parts_warehouse, workshop.workshop_warehouse):
			warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")
			if warehouse_company != transaction_company:
				frappe.throw(
					_("Warehouse {0} must belong to transaction company {1}.").format(
						warehouse, transaction_company
					)
				)

	@frappe.whitelist()
	def create_stock_entry(self, type="call"):
		from servicems.parts import post_parts

		self.check_permission("write")
		if self.is_new():
			frappe.throw(_("Save the Job Card before issuing parts."))
		from servicems.parts import allocations, lock_card

		card = lock_card(self.name)
		already_issued = {bucket["row"].service_part_row for bucket in allocations(card).values()}
		items = [
			{"part_row": row.name, "qty": row.qty}
			for row in card.parts
			if not row.use_existing_spares
			and not row.customer_supplied
			and row.qty
			and row.name not in already_issued
		]
		if not items:
			return
		return post_parts(self.name, "Issue", items, frappe.generate_hash(length=32))

	@frappe.whitelist()
	def create_invoice(self):
		from servicems.billing import make_invoice

		return make_invoice(self.name)

	def vaildate_complete(self):
		if self.status != "Completed":
			return

		for task in self.tasks:
			if not task.completed:
				frappe.throw(_("Row #{0}: The Tasks is not Completed").format(task.idx))

	def get_price_list(self, template_price_list=None):
		price_list = frappe.get_value("Customer", self.customer, "default_price_list")

		if not price_list and template_price_list:
			price_list = template_price_list

		if not price_list:
			price_list = frappe.get_value("Service Settings", "Service Settings", "price_list")
		return price_list or ""


def get_item_price(item_code, price_list, company):
	company_currency = frappe.get_value("Company", company, "default_currency")
	item_prices_data = frappe.db.get_value(
		"Item Price",
		filters={
			"price_list": price_list,
			"item_code": item_code,
			"currency": company_currency,
		},
		fieldname=["item_code", "price_list_rate", "currency"],
		as_dict=True,
		order_by="valid_from desc",
	)

	return item_prices_data.price_list_rate if item_prices_data else 0


@frappe.whitelist()
def get_selected_items(items, request_id):
	from servicems.parts import post_parts

	selected = frappe.parse_json(items)
	if not selected:
		frappe.throw(_("Select parts to return."))
	card = frappe.get_doc("Service Job Card", selected[0]["parent"])
	card.check_permission("write")
	request = []
	for value in selected:
		if value.get("parent") != card.name:
			frappe.throw(_("Select parts from one Job Card."))
		request.append({"issue_detail": value.get("issue_detail"), "qty": value.get("qty_to_return")})
	return post_parts(card.name, "Return", request, request_id)


@frappe.whitelist()
def get_all_supplied_parts(job_card):
	from servicems.parts import get_allocations

	return [
		dict(
			idx=idx,
			item=bucket["row"].item_code,
			item_name=bucket["row"].item_name,
			qty=bucket["outstanding"],
			rate=0,
			stock_entry=bucket["row"].stock_entry,
			issue_detail=detail,
			parent=job_card,
			parenttype="Service Job Card",
		)
		for idx, (detail, bucket) in enumerate(get_allocations(job_card).items(), 1)
		if bucket["outstanding"]
	]
