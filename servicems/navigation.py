"""Synchronize optional Bay navigation with native Frappe v16 Sidebar and Workspace."""

import json
from contextlib import contextmanager

import frappe


@contextmanager
def _navigation_write():
	"""Update app-owned navigation without exporting site-specific Bay state to JSON."""
	flags = {key: frappe.flags.get(key) for key in ("in_patch", "in_import")}
	frappe.flags.update(in_patch=True, in_import=True)
	try:
		yield
	finally:
		frappe.flags.update(flags)


def sync_bay_navigation():
	if not frappe.db.exists("DocType", "Service Settings"):
		return
	enabled = bool(frappe.db.get_single_value("Service Settings", "enable_bay_management"))
	if frappe.db.exists("DocType", "Sidebar") and frappe.db.exists("Sidebar", "Service Management"):
		sidebar = frappe.get_doc("Sidebar", "Service Management")
		items = [
			row.as_dict()
			for row in sidebar.items
			if not (row.link_type == "DocType" and row.link_to == "Bay")
		]
		if enabled:
			at = next((i for i, row in enumerate(items) if row.get("link_to") == "Service Workshop"), -1)
			bay = next(
				(
					row.as_dict()
					for row in sidebar.items
					if row.link_type == "DocType" and row.link_to == "Bay"
				),
				{},
			)
			bay.update(type="Link", label="Bays", link_type="DocType", link_to="Bay", child=1)
			items.insert(at + 1, bay)
		for idx, item in enumerate(items, 1):
			item["idx"] = idx
		if items != [row.as_dict() for row in sidebar.items]:
			sidebar.set("items", items)
			with _navigation_write():
				sidebar.save(ignore_permissions=True)
	if not frappe.db.exists("Workspace", "Service MS"):
		return
	workspace = frappe.get_doc("Workspace", "Service MS")
	blocks = json.loads(workspace.content or "[]")
	new_blocks = [block for block in blocks if block.get("data", {}).get("shortcut_name") != "Bays"]
	shortcuts = [row.as_dict() for row in workspace.shortcuts if row.label != "Bays"]
	if enabled:
		at = next(
			(
				i
				for i, block in enumerate(new_blocks)
				if block.get("data", {}).get("shortcut_name") == "Workshops"
			),
			-1,
		)
		new_blocks.insert(
			at + 1, {"id": "servicems_bay", "type": "shortcut", "data": {"shortcut_name": "Bays", "col": 3}}
		)
		bay = next((row.as_dict() for row in workspace.shortcuts if row.label == "Bays"), {})
		bay.update(
			label="Bays", type="DocType", link_to="Bay", doc_view="List", color="Grey", stats_filter="[]"
		)
		shortcuts.append(bay)
	if new_blocks != blocks or shortcuts != [row.as_dict() for row in workspace.shortcuts]:
		workspace.content = json.dumps(new_blocks)
		workspace.set("shortcuts", shortcuts)
		with _navigation_write():
			workspace.save(ignore_permissions=True)
