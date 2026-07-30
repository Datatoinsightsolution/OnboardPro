import frappe


def execute():
	"""The top tier reverted from 'Extreme' back to 'Urgent' — update existing records."""
	frappe.db.sql(
		"UPDATE `tabImplementation Request` SET priority = 'Urgent' WHERE priority = 'Extreme'"
	)
