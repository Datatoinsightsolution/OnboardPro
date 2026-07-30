import frappe
from frappe import _
from frappe.model import no_value_fields
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

STAFF_ROLES = {"Onboardpro Staff", "System Manager", "Administrator"}

# The only field a customer may ever change on a request. Everything else is staff-owned.
# See _guard_customer_writes for why this has to be enforced here rather than with `read_only`.
CUSTOMER_WRITABLE_FIELDS = {"delivery_date"}


def is_staff(user=None):
	return bool(set(frappe.get_roles(user or frappe.session.user)) & STAFF_ROLES)


def _as_date(value):
	"""Date or None — never today.

	frappe.utils.getdate(None) returns *today* rather than None, so every comparison
	in this module guards the empty case before calling it.
	"""
	return getdate(value) if value else None


def get_manager_company(user):
	"""Return the company `user` manages, or None if they aren't a Manager."""
	return frappe.db.get_value(
		"Onboardpro Customer", {"user": user, "designation": "Manager"}, "company"
	)


def get_company_customer_emails(company):
	"""Return every customer user (Manager or User) belonging to `company`."""
	return frappe.get_all("Onboardpro Customer", filters={"company": company}, pluck="user")


def get_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user
	if is_staff(user):
		return ""
	company = get_manager_company(user)
	if company:
		emails = get_company_customer_emails(company) or [user]
		in_clause = ", ".join(frappe.db.escape(e) for e in emails)
		return f"`tabImplementation Request`.`customer_email` in ({in_clause})"
	return f"`tabImplementation Request`.`customer_email` = {frappe.db.escape(user)}"


def has_permission(doc, ptype="read", user=None):
	if not user:
		user = frappe.session.user
	if is_staff(user):
		return True
	if doc.get("customer_email") == user:
		return ptype in ("read", "write")
	if ptype == "read":
		company = get_manager_company(user)
		if company:
			requester_company = frappe.db.get_value(
				"Onboardpro Customer", doc.get("customer_email"), "company"
			)
			return requester_company == company
	return False


class ImplementationRequest(Document):
	def before_insert(self):
		self.assignee = frappe.session.user
		self.assignee_name = frappe.db.get_value("User", frappe.session.user, "full_name")
		self._sync_customer_email()
		# Delivery is a commitment the customer makes *after* seeing the request.
		# Never accept it, or either stamp, from an insert payload.
		self.delivery_date = None
		self.delivery_committed_on = None
		self.resolved_on = None

	def validate(self):
		if self.has_value_changed("customer"):
			self._sync_customer_email()
		self._guard_customer_writes()
		self._validate_delivery_date()
		self._stamp_resolution()

	def _sync_customer_email(self):
		self.customer_email = self.customer or ""

	# ── Field-level authorisation ─────────────────────────────────────────────

	def _guard_customer_writes(self):
		"""Revert any field a non-staff user isn't allowed to touch.

		`read_only` on a docfield is a desk-form hint with no server-side effect, and
		frappe.client.set_value — the only write path this app's SPA uses — does a plain
		doc.update(values) on whatever the caller sends. Without this, a customer with
		doc-level write could set status="Resolved" and forge an on-time delivery.
		"""
		before = self.get_doc_before_save()
		if not before or is_staff():
			return
		for df in self.meta.fields:
			if df.fieldname in CUSTOMER_WRITABLE_FIELDS or df.fieldtype in no_value_fields:
				continue
			if self.get(df.fieldname) != before.get(df.fieldname):
				self.set(df.fieldname, before.get(df.fieldname))

	# ── Delivery commitment ───────────────────────────────────────────────────

	def _validate_delivery_date(self):
		before = self.get_doc_before_save()
		if not before:
			# Insert — before_insert already blanked these. (has_value_changed returns
			# True unconditionally when there is no _doc_before_save, so don't use it.)
			return

		old = _as_date(before.delivery_date)
		new = _as_date(self.delivery_date)

		if old == new:
			# Unchanged — re-assert the stamp so a payload can't forge or clear it.
			self.delivery_committed_on = before.delivery_committed_on
			return

		if not is_staff():
			if old:
				frappe.throw(
					_(
						"The delivery date has already been committed and cannot be changed. "
						"Ask your OnboardPro contact if it needs to be renegotiated."
					),
					frappe.PermissionError,
				)
			if not new:
				frappe.throw(_("Please choose a delivery date."))
			# First commitment — this is the milestone.
			self.delivery_committed_on = now_datetime()
			return

		# Staff amending, or committing on the customer's behalf. The milestone records
		# the *first* commitment only; renegotiation must not reset it.
		self.delivery_committed_on = before.delivery_committed_on or (now_datetime() if new else None)

	# ── Resolution stamp ──────────────────────────────────────────────────────

	def _stamp_resolution(self):
		"""Stamp the first resolution. Reopening never clears it, re-resolving never moves it."""
		before = self.get_doc_before_save()
		prior = before.resolved_on if before else None

		if prior:
			self.resolved_on = prior
		elif self.status == "Resolved":
			self.resolved_on = now_datetime()
		else:
			self.resolved_on = None
