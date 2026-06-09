import json
import os

import frappe


_ALLOWED_ROLES = {"Onboardpro Staff", "Onboardpro Customer"}


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/onboardpro"
		raise frappe.Redirect

	if not _ALLOWED_ROLES.intersection(set(frappe.get_roles())):
		frappe.throw("Not permitted", frappe.PermissionError)

	context.no_cache = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.session_user = frappe.session.user
	context.session_user_fullname = (
		frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	)

	# Resolve hashed Vite asset filenames from the build manifest
	manifest_path = frappe.get_app_path("onboardpro", "public", "frontend", "manifest.json")
	if os.path.exists(manifest_path):
		with open(manifest_path) as f:
			manifest = json.load(f)
		entry = manifest.get("index.html", {})
		context.js_file = "/assets/onboardpro/frontend/" + entry.get("file", "")
		# Collect CSS from entry and all imported chunks
		css, seen = [], set()

		def _collect_css(key):
			if key in seen:
				return
			seen.add(key)
			chunk = manifest.get(key, {})
			css.extend(chunk.get("css", []))
			for imp in chunk.get("imports", []):
				_collect_css(imp)

		_collect_css("index.html")
		context.css_files = ["/assets/onboardpro/frontend/" + c for c in css]
	else:
		context.js_file = ""
		context.css_files = []
