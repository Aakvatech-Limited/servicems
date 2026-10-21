"""Keep native v16 Workspace links aligned with optional Bay Management."""

import json

import frappe


def sync_bay_navigation():
	if not frappe.db.exists("DocType", "Workspace Sidebar"):
		return
	enabled = bool(frappe.db.get_single_value("Service Settings", "enable_bay_management"))
	if frappe.db.exists("Workspace Sidebar", "Service MS"):
		sidebar = frappe.get_doc("Workspace Sidebar", "Service MS")
		current = [row for row in sidebar.items if row.link_to != "Bay"]
		if enabled:
			current.append(frappe._dict({
				"type": "Link", "label": "Bays", "link_to": "Bay", "link_type": "DocType",
				"child": 0, "indent": 0, "collapsible": 0, "show_arrow": 0,
			}))
		if len(current) != len(sidebar.items) or enabled:
			sidebar.set("items", current)
			sidebar.save(ignore_permissions=True)
	if not frappe.db.exists("Workspace", "Service MS"):
		return
	workspace = frappe.get_doc("Workspace", "Service MS")
	blocks = json.loads(workspace.content or "[]")
	blocks = [block for block in blocks if block.get("data", {}).get("shortcut_name") != "Bay"]
	shortcuts = [row.as_dict() for row in workspace.shortcuts if row.label != "Bay"]
	if enabled:
		blocks.append({"id": "servicems_bay", "type": "shortcut", "data": {"shortcut_name": "Bay", "col": 3}})
		shortcuts.append({"label": "Bay", "type": "DocType", "link_to": "Bay", "doc_view": "List", "color": "Grey", "stats_filter": "[]"})
	workspace.content = json.dumps(blocks)
	workspace.set("shortcuts", shortcuts)
	workspace.save(ignore_permissions=True)
