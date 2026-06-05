import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from onboardpro.onboardpro.sla import apply_sla

STAFF_ROLES = {"Onboardpro Staff", "System Manager", "Administrator"}


def get_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user
	if set(frappe.get_roles(user)) & STAFF_ROLES:
		return ""
	return f"`tabImplementation Request`.`customer_email` = {frappe.db.escape(user)}"


def has_permission(doc, ptype="read", user=None):
	if not user:
		user = frappe.session.user
	if set(frappe.get_roles(user)) & STAFF_ROLES:
		return True
	if ptype in ("read", "write"):
		return doc.get("customer_email") == user
	return False


class ImplementationRequest(Document):
	def before_insert(self):
		self.assignee = frappe.session.user
		self.assignee_name = frappe.db.get_value("User", frappe.session.user, "full_name")
		self._sync_customer_email()
		apply_sla(self)

	def validate(self):
		if self.has_value_changed("customer"):
			self._sync_customer_email()
		apply_sla(self)

	def _sync_customer_email(self):
		self.customer_email = self.customer or ""
