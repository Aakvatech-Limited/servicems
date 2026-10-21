"""Synchronize optional Bay navigation with native Frappe v16 Sidebar and Workspace."""

import json

import frappe


def sync_bay_navigation():
	if not frappe.db.exists("DocType", "Service Settings"):
		return
	enabled = bool(frappe.db.get_single_value("Service Settings", "enable_bay_management"))
	if frappe.db.exists("DocType", "Sidebar") and frappe.db.exists("Sidebar", "Service Management"):
		sidebar = frappe.get_doc("Sidebar", "Service Management")
		items = [row.as_dict() for row in sidebar.items if not (row.link_type == "DocType" and row.link_to == "Bay")]
		if enabled:
			at = next((i for i, row in enumerate(items) if row.get("link_to") == "Service Workshop"), -1)
			items.insert(at + 1, {"type": "Link", "label": "Bays", "link_type": "DocType", "link_to": "Bay", "child": 1})
		if len(items) != len(sidebar.items) or enabled:
			sidebar.set("items", items)
			sidebar.save(ignore_permissions=True)
	if not frappe.db.exists("Workspace", "Service MS"):
		return
	workspace = frappe.get_doc("Workspace", "Service MS")
	blocks = json.loads(workspace.content or "[]")
	new_blocks = [block for block in blocks if block.get("data", {}).get("shortcut_name") != "Bays"]
	shortcuts = [row.as_dict() for row in workspace.shortcuts if row.label != "Bays"]
	if enabled:
		at = next((i for i, block in enumerate(new_blocks) if block.get("data", {}).get("shortcut_name") == "Workshops"), -1)
		new_blocks.insert(at + 1, {"id": "servicems_bay", "type": "shortcut", "data": {"shortcut_name": "Bays", "col": 3}})
		shortcuts.append({"label": "Bays", "type": "DocType", "link_to": "Bay", "doc_view": "List", "color": "Grey", "stats_filter": "[]"})
	if new_blocks != blocks or enabled:
		workspace.content = json.dumps(new_blocks)
		workspace.set("shortcuts", shortcuts)
		workspace.save(ignore_permissions=True)
