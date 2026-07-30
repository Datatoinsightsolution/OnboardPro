import frappe


def execute():
	"""The 'Urgent' priority/complexity tier was renamed to 'Extreme' — update existing records."""
	frappe.db.sql("UPDATE `tabImplementation Request` SET priority = 'Extreme' WHERE priority = 'Urgent'")
