import frappe
from frappe.model.document import Document


class SLAPolicy(Document):
	def validate(self):
		if self.is_default:
			frappe.db.set_value(
				"SLA Policy",
				{"name": ["!=", self.name], "is_default": 1},
				"is_default",
				0,
			)
