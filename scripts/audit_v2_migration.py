"""Audit a disposable Frappe site; run from bench/sites with the selected app on PYTHONPATH."""

import argparse
import json
from pathlib import Path

import frappe


def normalized(value):
	return json.loads(json.dumps(value, default=str))


def legacy_seed(snapshot_path):
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	from servicems.tests import utils

	if not frappe.db.exists("Warehouse Type", "Transit"):
		from erpnext.setup.setup_wizard.operations.install_fixtures import install

		install(country="United States")
	if not frappe.db.exists(
		"Fiscal Year",
		{"year_start_date": ["<=", frappe.utils.nowdate()], "year_end_date": [">=", frappe.utils.nowdate()]},
	):
		year = frappe.utils.nowdate()[:4]
		frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": f"_Test SMS {year}",
				"year_start_date": f"{year}-01-01",
				"year_end_date": f"{year}-12-31",
			}
		).insert()
	utils.create_test_data()
	utils.receive_stock()
	create_custom_fields(
		{
			"Service Job Card": [
				{
					"fieldname": "custom_legacy_note",
					"label": "Customer Technician Note",
					"fieldtype": "Data",
					"insert_after": "vin",
				}
			]
		}
	)
	frappe.get_doc(
		{
			"doctype": "Property Setter",
			"doc_type": "Service Job Card",
			"doctype_or_field": "DocField",
			"field_name": "vin",
			"property": "label",
			"property_type": "Data",
			"value": "Customer VIN",
		}
	).insert()
	card = utils.make_job_card(bay=utils.BAY)
	card.custom_legacy_note = "Legacy technician allocation retained"
	card.save()
	completed = utils.complete_tasks(utils.make_job_card(bay=utils.BAY))
	completed.save()
	completed.submit()
	utils.make_booking()
	workspace = frappe.get_doc("Workspace", "Service MS")
	workspace.type = "Workspace"
	blocks = json.loads(workspace.content)
	blocks.extend(
		[
			{"id": "customer_header", "type": "header", "data": {"text": "Customer Operations", "col": 12}},
			{
				"id": "customer_link",
				"type": "shortcut",
				"data": {"shortcut_name": "Customer lookup", "col": 3},
			},
		]
	)
	workspace.content = json.dumps(blocks)
	workspace.append(
		"shortcuts",
		{"label": "Customer lookup", "type": "DocType", "link_to": "Customer", "doc_view": "List"},
	)
	workspace.save(ignore_permissions=True)
	frappe.db.commit()
	snapshot = {
		"tables": {},
		"settings": frappe.db.get_singles_dict("Service Settings"),
		"workspace": workspace.as_dict(),
		"submitted_card": completed.name,
	}
	for row in frappe.get_all(
		"DocType", filters={"module": "Service Management", "issingle": 0}, fields=["name"]
	):
		snapshot["tables"][row.name] = frappe.get_all(row.name, fields=["*"], order_by="name")
	for doctype in (
		"Sales Invoice",
		"Sales Invoice Item",
		"Stock Entry",
		"Stock Entry Detail",
		"Stock Ledger Entry",
		"GL Entry",
	):
		snapshot["tables"][doctype] = frappe.get_all(doctype, fields=["*"], order_by="name")
	snapshot_path.write_text(json.dumps(snapshot, default=str, indent=2))
	print(
		"LEGACY SEEDED",
		{
			"tables": len(snapshot["tables"]),
			"records": sum(len(rows) for rows in snapshot["tables"].values()),
			"submitted_card": completed.name,
			"invoice": completed.invoice,
		},
	)


def verify_upgrade(snapshot_path):
	snapshot = json.loads(snapshot_path.read_text())
	for doctype, old_rows in snapshot["tables"].items():
		current = {
			row["name"]: row for row in normalized(frappe.get_all(doctype, fields=["*"], order_by="name"))
		}
		assert len(current) == len(old_rows), doctype
		for old in old_rows:
			assert old == {field: current[old["name"]][field] for field in old}, (doctype, old["name"])
	settings = frappe.db.get_singles_dict("Service Settings")
	for field, value in snapshot["settings"].items():
		if field not in ("modified", "modified_by"):
			assert settings.get(field) == value, field
	assert frappe.db.get_single_value("Service Settings", "enable_bay_management") == 1
	assert not frappe.db.get_single_value("Service Settings", "require_final_quality_check")
	assert frappe.get_meta("Service Job Card").has_field("custom_legacy_note")
	assert frappe.get_meta("Service Job Card").get_field("vin").label == "Customer VIN"
	backups = Path(frappe.get_site_path("backups", "servicems-navigation"))
	assert any("Customer Operations" in path.read_text() for path in backups.glob("*.json"))
	assert frappe.db.get_value("Service Job Card", snapshot["submitted_card"], "docstatus") == 1
	print(
		"UPGRADE VERIFIED",
		{
			"tables": len(snapshot["tables"]),
			"records": sum(len(rows) for rows in snapshot["tables"].values()),
			"custom_field": True,
			"property_setter": True,
			"customer_workspace_archived": True,
		},
	)


def verify_idempotence(site):
	from frappe.migrate import SiteMigration

	def state():
		records = {
			doctype: frappe.get_doc(doctype, name).as_dict()
			for doctype, name in (("Workspace", "Service MS"), ("Sidebar", "Service Management"))
		}
		records["settings"] = frappe.db.get_singles_dict("Service Settings")
		records["patches"] = frappe.db.count("Patch Log")
		directory = Path(frappe.get_site_path("backups", "servicems-navigation"))
		records["backups"] = sorted(path.name for path in directory.glob("*.json"))
		return normalized(records)

	before = state()
	for repeat in range(2):
		frappe.destroy()
		SiteMigration(skip_search_index=True).run(site=site)
		frappe.init(site=site, sites_path=".")
		frappe.connect()
		assert state() == before, (
			f"Migration {repeat + 1} changed navigation, settings, patch count or backups"
		)
	print(
		"IDEMPOTENCE VERIFIED: two full repeated migrations; navigation, settings, patch count and backups unchanged"
	)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"phase",
		choices=["fresh-install", "legacy-install", "legacy-seed", "verify-upgrade", "idempotence", "test"],
	)
	parser.add_argument("--site", required=True)
	parser.add_argument("--snapshot", type=Path)
	args = parser.parse_args()
	if args.phase in ("legacy-seed", "verify-upgrade") and args.snapshot is None:
		parser.error("--snapshot is required for this phase")
	frappe.init(site=args.site, sites_path=".")
	frappe.connect()
	try:
		if not frappe.conf.allow_tests:
			raise RuntimeError("Use a disposable audit site with allow_tests enabled")
		if args.phase in ("fresh-install", "legacy-install"):
			from frappe.installer import install_app

			if args.phase == "legacy-install":
				install_app("erpnext")
			install_app("servicems")
			if args.phase == "fresh-install":
				assert "erpnext" in frappe.get_installed_apps()
				assert frappe.db.exists("Sidebar", "Service Management")
				assert frappe.db.get_value("Workspace", "Service MS", "standard")
				assert not frappe.db.get_single_value("Service Settings", "enable_bay_management")
				assert not frappe.db.get_single_value("Service Settings", "require_final_quality_check")
				assert not frappe.get_meta("Service Booking").get_field("bay").reqd
			frappe.db.commit()
			print(args.phase.upper(), "VERIFIED")
		elif args.phase == "legacy-seed":
			legacy_seed(args.snapshot)
		elif args.phase == "verify-upgrade":
			verify_upgrade(args.snapshot)
		elif args.phase == "idempotence":
			verify_idempotence(args.site)
		else:
			import unittest

			loader = unittest.defaultTestLoader
			suite = unittest.TestSuite(
				loader.loadTestsFromName(module)
				for module in (
					"servicems.tests.test_navigation",
					"servicems.tests.test_migration_compatibility",
				)
			)
			if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
				raise SystemExit(1)
	finally:
		frappe.db.rollback()
		frappe.clear_cache()
		frappe.destroy()


if __name__ == "__main__":
	main()
