import frappe
from frappe import _


@frappe.whitelist()
def search_customers(query: str = "", limit: int = 500):
	"""Return enabled Users who have the Onboardpro Customer role."""
	like = f"%{query}%" if query else "%"
	return frappe.db.sql(
		"""
		SELECT u.name, u.full_name AS customer_name
		FROM `tabUser` u
		INNER JOIN `tabHas Role` hr
			ON hr.parent = u.name AND hr.parenttype = 'User' AND hr.role = 'Onboardpro Customer'
		WHERE u.enabled = 1
		  AND u.full_name LIKE %(like)s
		ORDER BY u.full_name
		LIMIT %(limit)s
		""",
		{"like": like, "limit": int(limit)},
		as_dict=True,
	)


@frappe.whitelist()
def get_activity(docname: str):
	"""Return merged activity (comments + status changes) for an Implementation Request."""
	frappe.has_permission("Implementation Request", ptype="read", doc=docname, throw=True)

	events = []

	# ── Comments ──────────────────────────────────────────────────────────────
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Implementation Request",
			"reference_name": docname,
			"comment_type": "Comment",
		},
		fields=["name", "content", "owner", "creation"],
		order_by="creation asc",
	)

	STAFF = {"Onboardpro Staff"}
	user_cache = {}

	def _user(email):
		if email not in user_cache:
			user_cache[email] = {
				"name": frappe.db.get_value("User", email, "full_name") or email,
				"is_staff": bool(set(frappe.get_roles(email)) & STAFF),
			}
		return user_cache[email]

	for c in comments:
		u = _user(c.owner)
		events.append(
			{
				"kind": "msg",
				"name": c.name,
				"content": c.content,
				"owner": c.owner,
				"owner_name": u["name"],
				"is_staff": u["is_staff"],
				"creation": str(c.creation),
			}
		)

	# ── Status changes from Version history ───────────────────────────────────
	STATUS_TONE = {
		"Open": "blue",
		"Awaiting Data": "amber",
		"In Review": "violet",
		"Needs Revision": "red",
		"Resolved": "green",
	}
	STATUS_ICON = {
		"Resolved": "check-circle",
		"Needs Revision": "alert-circle",
		"In Review": "eye",
		"Awaiting Data": "clock",
		"Open": "refresh-cw",
	}

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Implementation Request", "docname": docname},
		fields=["name", "owner", "creation", "data"],
		order_by="creation asc",
	)

	for v in versions:
		try:
			changed = frappe.parse_json(v.data).get("changed", [])
		except Exception:
			continue
		for field, old_val, new_val in changed:
			if field == "status":
				u = _user(v.owner)
				events.append(
					{
						"kind": "status",
						"name": f"{v.name}_status",
						"owner": v.owner,
						"owner_name": u["name"],
						"old_status": old_val,
						"new_status": new_val,
						"creation": str(v.creation),
						"tone": STATUS_TONE.get(new_val, "slate"),
						"icon": STATUS_ICON.get(new_val, "refresh-cw"),
						"html": (
							f'<b>{frappe.utils.escape_html(u["name"])}</b> changed status from '
							f'<b>{frappe.utils.escape_html(old_val)}</b> → '
							f'<b>{frappe.utils.escape_html(new_val)}</b>'
						),
					}
				)

			elif field == "delivery_date":
				u = _user(v.owner)
				actor = frappe.utils.escape_html(u["name"])
				new_txt = frappe.utils.escape_html(frappe.utils.formatdate(new_val)) or "—"
				if old_val:
					old_txt = frappe.utils.escape_html(frappe.utils.formatdate(old_val))
					html = (
						f"<b>{actor}</b> moved the delivery date from "
						f"<b>{old_txt}</b> → <b>{new_txt}</b>"
					)
					tone, icon = "amber", "edit-3"
				else:
					html = f"<b>{actor}</b> committed a delivery date of <b>{new_txt}</b>"
					tone, icon = "green", "calendar"
				events.append(
					{
						"kind": "delivery",
						"name": f"{v.name}_delivery_date",
						"owner": v.owner,
						"owner_name": u["name"],
						"old_date": old_val,
						"new_date": new_val,
						"creation": str(v.creation),
						"tone": tone,
						"icon": icon,
						"html": html,
					}
				)

			elif field == "expected_date" and old_val:
				u = _user(v.owner)
				events.append(
					{
						"kind": "expected",
						"name": f"{v.name}_expected_date",
						"owner": v.owner,
						"owner_name": u["name"],
						"creation": str(v.creation),
						"tone": "slate",
						"icon": "calendar",
						"html": (
							f'<b>{frappe.utils.escape_html(u["name"])}</b> changed the expected date from '
							f"<b>{frappe.utils.escape_html(frappe.utils.formatdate(old_val))}</b> → "
							f"<b>{frappe.utils.escape_html(frappe.utils.formatdate(new_val))}</b>"
						),
					}
				)

	# ── Delivery verdict on resolution ────────────────────────────────────────
	req = frappe.db.get_value(
		"Implementation Request",
		docname,
		["status", "delivery_date", "resolved_on"],
		as_dict=True,
	)
	if req and req.status == "Resolved" and req.resolved_on and req.delivery_date:
		days = frappe.utils.date_diff(req.resolved_on, req.delivery_date)
		late = days > 0
		events.append(
			{
				"kind": "verdict",
				"name": f"{docname}_verdict",
				"owner": "",
				"owner_name": "",
				"creation": str(req.resolved_on),
				"tone": "amber" if late else "green",
				"icon": "clock" if late else "check-circle",
				"html": (
					f"Delivered <b>{days} day{'s' if days != 1 else ''} late</b> "
					"against the committed date"
				)
				if late
				else "Delivered <b>on time</b> against the committed date",
			}
		)

	events.sort(key=lambda x: x["creation"])
	return events


@frappe.whitelist()
def get_attachments(docname: str):
	"""Return files attached to an Implementation Request.

	Core Frappe's File doctype only lets non-desk users (both our Onboardpro Staff and
	Onboardpro Customer roles have desk_access=0) list files they personally own — see
	frappe.core.doctype.file.file.get_permission_query_conditions. That hides attachments
	the other party on the same request uploaded. We authorize against the parent request
	instead and fetch the files directly, bypassing File's own permission query.
	"""
	frappe.has_permission("Implementation Request", ptype="read", doc=docname, throw=True)

	return frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Implementation Request", "attached_to_name": docname},
		fields=["name", "file_name", "file_url", "file_size", "creation", "attached_to_name"],
		order_by="creation asc",
		ignore_permissions=True,
	)


@frappe.whitelist()
def add_comment(docname: str, content: str):
	"""Insert a comment on behalf of the logged-in user after verifying request access."""
	frappe.has_permission("Implementation Request", ptype="read", doc=docname, throw=True)

	comment = frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "Implementation Request",
			"reference_name": docname,
			"content": content,
			"owner": frappe.session.user,
		}
	)
	comment.insert(ignore_permissions=True)
	frappe.db.commit()

	sender_roles = set(frappe.get_roles(frappe.session.user))
	is_customer = not bool(sender_roles & {"Onboardpro Staff"})

	if is_customer:
		# Stamp last customer reply so staff can see unread indicator
		frappe.db.set_value(
			"Implementation Request",
			docname,
			"last_customer_reply",
			frappe.utils.now_datetime(),
			update_modified=False,
		)
		frappe.db.commit()

	return comment.as_dict()


@frappe.whitelist()
def mark_seen(docname: str):
	"""Record that the current user has viewed this request (persisted in cache for 30 days)."""
	cache_key = f"risto_seen_{frappe.session.user}"
	seen_map = frappe.cache.get_value(cache_key) or {}
	# Use str(now_datetime()) — same "YYYY-MM-DD HH:MM:SS" format as DB, so string comparison works
	seen_map[docname] = str(frappe.utils.now_datetime())
	frappe.cache.set_value(cache_key, seen_map, expires_in_sec=86400 * 30)


@frappe.whitelist()
def get_unread_requests():
	"""
	Return names of requests that have a customer reply newer than the current
	user last viewed them. Only meaningful for staff.
	"""
	roles = set(frappe.get_roles())
	if not (roles & {"Onboardpro Staff"}):
		return []

	cache_key = f"risto_seen_{frappe.session.user}"
	seen_map = frappe.cache.get_value(cache_key) or {}

	with_reply = frappe.get_all(
		"Implementation Request",
		filters={"last_customer_reply": ["is", "set"]},
		fields=["name", "last_customer_reply"],
	)

	unread = []
	for req in with_reply:
		last_seen = seen_map.get(req.name)
		reply_ts = str(req.last_customer_reply)
		if not last_seen or reply_ts > last_seen:
			unread.append(req.name)

	return unread


@frappe.whitelist()
def get_comments(docname: str):
	"""Return comments for an Implementation Request with resolved owner full names."""
	frappe.has_permission("Implementation Request", doc=docname, throw=True)

	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Implementation Request",
			"reference_name": docname,
			"comment_type": "Comment",
		},
		fields=["name", "content", "owner", "creation", "comment_type"],
		order_by="creation asc",
	)

	# Batch-resolve owner full names and staff status
	unique_owners = {c.owner for c in comments}
	STAFF = {"Onboardpro Staff"}
	user_info = {}
	for email in unique_owners:
		roles = set(frappe.get_roles(email))
		user_info[email] = {
			"owner_name": frappe.db.get_value("User", email, "full_name") or email,
			"is_staff": bool(roles & STAFF),
		}

	for c in comments:
		info = user_info[c.owner]
		c.owner_name = info["owner_name"]
		c.is_staff = info["is_staff"]

	return comments


@frappe.whitelist()
def get_session_role():
	"""Return role and display name for the logged-in user."""
	roles = set(frappe.get_roles())
	if not roles & {"Onboardpro Staff", "Onboardpro Customer"}:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	role = "staff" if "Onboardpro Staff" in roles else "customer"
	full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	# Ship the server's date so the SPA buckets requests against system time, not browser time.
	result = {"role": role, "full_name": full_name, "today": frappe.utils.today()}

	if role == "customer":
		profile = frappe.db.get_value(
			"Onboardpro Customer", frappe.session.user, ["company", "designation"], as_dict=True
		)
		result["company"] = profile.company if profile else None
		result["is_manager"] = bool(profile and profile.designation == "Manager")

	return result


@frappe.whitelist()
def has_app_permission():
	"""Return True if the current user has access to the OnboardPro app."""
	return bool({"Onboardpro Staff", "Onboardpro Customer"}.intersection(set(frappe.get_roles())))


def _require_staff():
	if "Onboardpro Staff" not in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_company_hierarchy():
	"""Return every company with its assigned customers, for the admin hierarchy screen."""
	_require_staff()

	companies = frappe.get_all(
		"Onboardpro Company", fields=["name", "company_name"], order_by="company_name"
	)
	members = frappe.get_all(
		"Onboardpro Customer",
		fields=["user", "customer_name", "company", "designation"],
		order_by="designation asc, customer_name asc",
	)

	by_company = {}
	for m in members:
		by_company.setdefault(m.company, []).append(m)

	for c in companies:
		c["members"] = by_company.get(c.name, [])

	return companies


@frappe.whitelist()
def assign_customer(user: str, company: str, designation: str = "User"):
	"""Create or update the Onboardpro Customer profile for `user` (staff only)."""
	_require_staff()

	if designation not in ("Manager", "User"):
		frappe.throw(_("Invalid designation"))
	if not frappe.db.exists("Onboardpro Company", company):
		frappe.throw(_("Unknown company"))

	if frappe.db.exists("Onboardpro Customer", user):
		doc = frappe.get_doc("Onboardpro Customer", user)
		doc.company = company
		doc.designation = designation
		doc.save()
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Onboardpro Customer",
				"user": user,
				"company": company,
				"designation": designation,
			}
		)
		doc.insert()

	return doc.as_dict()


# ── Delivery dashboard ────────────────────────────────────────────────────────

DASHBOARD_FIELDS = [
	"name",
	"subject",
	"customer",
	"customer_name",
	"status",
	"priority",
	"expected_date",
	"delivery_date",
	"delivery_committed_on",
	"resolved_on",
	"creation",
]


# Open states that need chasing — red on the dashboard, and what the Overdue tab and the
# sidebar badge count. Two different failures: "broke the promise" vs "never made one".
ATTENTION_STATES = ("overdue", "nocommit")


def _delivery_state(req, today):
	"""Bucket a request against its dates.

	Mirrors deliveryState() in frontend/src/utils/helpers.js — keep the two in sync.
	"""
	if not req.delivery_date:
		# Resolved without a commitment (legacy rows) is settled, not a red flag.
		if req.status == "Resolved":
			return "awaiting"
		# Past the date staff needed the data by, and the customer still hasn't
		# committed to anything. getdate(None) returns *today*, so guard the empty case.
		expected = frappe.utils.getdate(req.expected_date) if req.expected_date else None
		return "nocommit" if expected and today > expected else "awaiting"

	due = frappe.utils.getdate(req.delivery_date)

	if req.status == "Resolved":
		# resolved_on is always set for a Resolved request (stamped in validate), but
		# fall back to today rather than trusting that on a legacy row.
		done = frappe.utils.getdate(req.resolved_on) if req.resolved_on else today
		return "late" if done > due else "ontime"

	return "overdue" if today > due else "ontrack"


@frappe.whitelist()
def get_dashboard():
	"""Delivery-commitment dashboard, for both staff and customers.

	There is deliberately no role branch and no customer filter here: frappe.get_list
	runs the `permission_query_conditions` hook registered for Implementation Request,
	so staff see everything, a company Manager sees their company, and a plain customer
	sees only their own rows. frappe.get_all would NOT — it forces ignore_permissions.
	"""
	if not {"Onboardpro Staff", "Onboardpro Customer"} & set(frappe.get_roles()):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	today = frappe.utils.getdate(frappe.utils.today())

	rows = frappe.get_list(
		"Implementation Request",
		fields=DASHBOARD_FIELDS,
		order_by="delivery_date asc, expected_date asc",
		limit_page_length=0,  # get_list defaults to 20
	)

	counts = {"awaiting": 0, "nocommit": 0, "ontrack": 0, "overdue": 0, "late": 0, "ontime": 0}
	slip_total = slip_n = 0
	watchlist = []

	for r in rows:
		state = _delivery_state(r, today)
		r["delivery_state"] = state
		counts[state] += 1

		# date_diff takes the END date first. For nocommit the blown date is the
		# expected date, since there is no commitment to measure against.
		if state == "overdue":
			r["days_overdue"] = frappe.utils.date_diff(today, r.delivery_date)
		elif state == "nocommit":
			r["days_overdue"] = frappe.utils.date_diff(today, r.expected_date)
		elif state == "late":
			r["days_late"] = frappe.utils.date_diff(r.resolved_on, r.delivery_date)

		if r.status != "Resolved":
			watchlist.append(r)

		if r.delivery_date and r.expected_date:
			slip_total += frappe.utils.date_diff(r.delivery_date, r.expected_date)
			slip_n += 1

	# Needs-chasing first, then by whichever date is the live one for that state.
	rank = {"overdue": 0, "nocommit": 1, "ontrack": 2, "awaiting": 3}
	watchlist.sort(
		key=lambda r: (
			rank.get(r.delivery_state, 9),
			str(r.delivery_date or r.expected_date or "9999-12-31"),
		)
	)

	settled = counts["ontime"] + counts["late"]
	return {
		"today": str(today),
		"total": len(rows),
		"open": sum(1 for r in rows if r.status != "Resolved"),
		"counts": counts,
		"attention": sum(counts[s] for s in ATTENTION_STATES),
		"on_time_rate": round(100.0 * counts["ontime"] / settled) if settled else None,
		"avg_commitment_slip": round(slip_total / slip_n, 1) if slip_n else None,
		"watchlist": watchlist[:10],
	}
