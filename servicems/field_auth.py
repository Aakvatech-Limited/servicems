from urllib.parse import urlencode, urlsplit

import frappe


def login_url():
	return "/field-login?" + urlencode({"redirect-to": "/field"})


def login_context(context):
	from frappe.www.login import get_context

	user = frappe.session.user
	try:
		# Build the native public login options without its signed-in redirect.
		frappe.session.user = "Guest"
		context = get_context(context)
		context["logo"] = "/assets/servicems/field/icon-192.png"
		return context
	finally:
		frappe.session.user = user


def record_field_login(login_manager):
	if frappe.session.user == "Guest":
		return
	referrer = urlsplit(frappe.request.referrer or "")
	if referrer.netloc == frappe.request.host and referrer.path == "/field-login":
		frappe.session.data.servicems_field_login = True
		frappe.local.session_obj.update(force=True)
