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
			if field != "status":
				continue
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

	# ── First response event ──────────────────────────────────────────────────
	first_responded_on = frappe.db.get_value("Implementation Request", docname, "first_responded_on")
	if first_responded_on:
		customer = frappe.db.get_value("Implementation Request", docname, "customer")
		u = _user(customer) if customer else {"name": "Customer", "is_staff": False}
		events.append(
			{
				"kind": "status",
				"name": f"{docname}_first_response",
				"owner": customer or "",
				"owner_name": u["name"],
				"creation": str(first_responded_on),
				"tone": "green",
				"icon": "check-circle",
				"html": f'<b>{frappe.utils.escape_html(u["name"])}</b> replied for the first time — FR SLA fulfilled',
			}
		)

	events.sort(key=lambda x: x["creation"])
	return events


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
		# Stamp first-response SLA
		from onboardpro.onboardpro.sla import set_first_response

		set_first_response(docname)

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
def get_sla_config():
	"""Return priority SLA times from the active default policy, for display in the create dialog."""
	policy_name = frappe.db.get_value(
		"SLA Policy", {"is_default": 1, "enabled": 1}, "name"
	) or frappe.db.get_value("SLA Policy", {"enabled": 1}, "name")
	if not policy_name:
		return {}

	rows = frappe.get_all(
		"SLA Priority",
		filters={"parent": policy_name},
		fields=["priority", "response_time", "resolution_time"],
	)
	return {r.priority: {"frH": r.response_time, "resH": r.resolution_time} for r in rows}


@frappe.whitelist()
def get_session_role():
	"""Return role and display name for the logged-in user."""
	roles = set(frappe.get_roles())
	if not roles & {"Onboardpro Staff", "Onboardpro Customer"}:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	role = "staff" if "Onboardpro Staff" in roles else "customer"
	full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	return {"role": role, "full_name": full_name}


@frappe.whitelist()
def has_app_permission():
	"""Return True if the current user has access to the OnboardPro app."""
	return bool({"Onboardpro Staff", "Onboardpro Customer"}.intersection(set(frappe.get_roles())))
