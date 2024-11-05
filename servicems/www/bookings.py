from __future__ import unicode_literals
import frappe
from frappe.utils.telemetry import capture

cache = 1

def get_context():
    frappe.db.commit()
    context = frappe._dict()
    context.boot = get_boot()
    if frappe.session.user != "Guest":
        capture("active_site", "bookings")

    return context

def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "default_route": "/bookings",
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "csrf_token": frappe.sessions.get_csrf_token(),
        }
    )

