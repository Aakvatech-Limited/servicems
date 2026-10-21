import json
import os
from datetime import datetime, timezone
from pathlib import Path

import frappe


def backup_navigation():
	"""Keep the previous records, including an explicit marker for a missing sidebar."""
	records = {}
	for doctype, name in (("Workspace", "Service MS"), ("Sidebar", "Service Management")):
		records[doctype] = (
			frappe.get_doc(doctype, name).as_dict() if frappe.db.exists(doctype, name) else None
		)
	path = Path(frappe.get_site_path("backups", "servicems-navigation"))
	path.mkdir(parents=True, exist_ok=True)
	stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
	backup = path / f"{stamp}.json"
	fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
	with os.fdopen(fd, "w") as handle:
		json.dump(records, handle, default=str, indent=2)
	return backup


def execute():
	"""Replace legacy navigation once, even when the site's timestamp is newer."""
	from servicems.navigation import sync_bay_navigation

	backup_navigation()
	frappe.reload_doc("service_management", "workspace", "service_ms", force=True)
	frappe.reload_doc("service_management", "sidebar", "service_management", force=True)
	sync_bay_navigation()
