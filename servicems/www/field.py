"""Private online Field Operations entry, authenticated by the Frappe session."""

import frappe

from servicems.field_auth import login_url

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest" or not frappe.session.data.get("servicems_field_login"):
		frappe.local.flags.redirect_location = login_url()
		raise frappe.Redirect
	context.no_cache = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.field_user = frappe.session.user
	return context
