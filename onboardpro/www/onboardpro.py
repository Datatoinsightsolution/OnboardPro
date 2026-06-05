import json
import os

import frappe


def get_context(context):
	if frappe.session.user == "Guest":
		redirect = frappe.utils.get_url("/onboardpro")
		frappe.local.flags.redirect_location = f"/login?redirect-to=/onboardpro"
		raise frappe.Redirect

	context.no_cache = 1
	context.show_sidebar = 0
	context.title = "Risto — Implementation Portal"

	# Resolve hashed Vite asset filenames from the build manifest
	manifest_path = frappe.get_app_path("onboardpro", "public", "frontend", ".vite", "manifest.json")
	if os.path.exists(manifest_path):
		with open(manifest_path) as f:
			manifest = json.load(f)
		entry = manifest.get("index.html", {})
		context.js_file = "/assets/onboardpro/frontend/" + entry.get("file", "")
		context.css_files = ["/assets/onboardpro/frontend/" + c for c in entry.get("css", [])]
	else:
		context.js_file = ""
		context.css_files = []
