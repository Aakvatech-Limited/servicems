import json
import unittest

import frappe
from frappe.model.sync import get_doc_files
from frappe.modules.import_file import import_doc, import_file_by_path

from servicems.navigation import sync_bay_navigation
from servicems.patches.v2_0.sync_v16_navigation import backup_navigation, execute

SECTIONS = [
	"Daily Operations",
	"Workshop Management",
	"Vehicles & Service Masters",
	"Parts & Inventory",
	"Reports & Monitoring",
	"Configuration",
]


class TestNavigation(unittest.TestCase):
	"""Run with an initialized Frappe site; roll back every navigation write."""

	def setUp(self):
		frappe.db.savepoint("servicems_navigation_test")
		self.flags = dict(frappe.flags)
		self.addCleanup(self.restore_site)

	def restore_site(self):
		frappe.db.rollback(save_point="servicems_navigation_test")
		frappe.flags.clear()
		frappe.flags.update(self.flags)
		frappe.clear_cache()

	def test_framework_discovers_both_standard_documents(self):
		files = get_doc_files([], frappe.get_app_path("servicems", "service_management"))
		for doctype, name in (("workspace", "service_ms"), ("sidebar", "service_management")):
			path = frappe.get_app_path("servicems", "service_management", doctype, name, f"{name}.json")
			self.assertIn(path, files)
			with open(path) as handle:
				definition = json.load(handle)
			self.assertEqual(definition["standard"], 1)

	def test_upgrade_replaces_and_backs_up_newer_legacy_workspace(self):
		# The deployed site has newer, non-standard records that normal migrate skips.
		legacy = frappe.get_doc("Workspace", "Service MS").as_dict()
		legacy.update(
			standard=0,
			links=[],
			shortcuts=[
				{
					"label": "Booking Page",
					"type": "URL",
					"url": "/bookings",
				}
			],
			content='[{"type":"header","data":{"text":"legacy"}}]',
		)
		import_doc(legacy, ignore_version=True)
		frappe.db.set_value(
			"Workspace", "Service MS", "modified", "2099-01-01 00:00:00", update_modified=False
		)
		path = frappe.get_app_path(
			"servicems", "service_management", "workspace", "service_ms", "service_ms.json"
		)
		self.assertFalse(import_file_by_path(path))
		backup = backup_navigation()
		self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
		self.assertEqual(json.loads(backup.read_text())["Workspace"]["shortcuts"][0]["label"], "Booking Page")
		execute()
		workspace = frappe.get_doc("Workspace", "Service MS")
		self.assertEqual(workspace.standard, 1)
		self.assertEqual(workspace.type, "Workspace")
		self.assertEqual(
			[b["data"]["text"] for b in json.loads(workspace.content) if b["type"] == "header"], SECTIONS
		)
		self.assertNotIn("Booking Page", [row.label for row in workspace.shortcuts])

	def test_upgrade_creates_missing_native_sidebar(self):
		if frappe.db.exists("Sidebar", "Service Management"):
			frappe.delete_doc("Sidebar", "Service Management", ignore_permissions=True, force=True)
		execute()
		sidebar = frappe.get_doc("Sidebar", "Service Management")
		self.assertEqual(sidebar.standard, 1)
		self.assertEqual(sidebar.module, "Service Management")
		self.assertEqual([row.label for row in sidebar.items if row.type == "Section Break"], SECTIONS)

	def test_bay_toggle_is_idempotent_and_restores_write_flags(self):
		execute()
		for enabled in (0, 1, 1, 0):
			flags = {key: frappe.flags.get(key) for key in ("in_patch", "in_import")}
			settings = frappe.get_doc("Service Settings")
			settings.enable_bay_management = enabled
			# Legacy sites can have an unset price list; keep unrelated settings untouched.
			settings.flags.ignore_mandatory = True
			settings.save(ignore_permissions=True)
			self.assertEqual({key: frappe.flags.get(key) for key in flags}, flags)
			workspace = frappe.get_doc("Workspace", "Service MS")
			sidebar = frappe.get_doc("Sidebar", "Service Management")
			self.assertEqual(sum(row.link_to == "Bay" for row in sidebar.items), enabled)
			self.assertEqual(sum(row.link_to == "Bay" for row in workspace.shortcuts), enabled)
			self.assertEqual(
				sum(b.get("data", {}).get("shortcut_name") == "Bays" for b in json.loads(workspace.content)),
				enabled,
			)
			modified = (workspace.modified, sidebar.modified)
			sync_bay_navigation()
			self.assertEqual(
				(
					frappe.get_doc("Workspace", "Service MS").modified,
					frappe.get_doc("Sidebar", "Service Management").modified,
				),
				modified,
			)

	def test_all_navigation_targets_exist(self):
		execute()
		workspace = frappe.get_doc("Workspace", "Service MS")
		sidebar = frappe.get_doc("Sidebar", "Service Management")
		for row in [*workspace.shortcuts, *[item for item in sidebar.items if item.type == "Link"]]:
			kind = row.type if row.doctype == "Workspace Shortcut" else row.link_type
			self.assertIn(kind, ("DocType", "Report"))
			self.assertTrue(frappe.db.exists(kind, row.link_to), (kind, row.link_to))
