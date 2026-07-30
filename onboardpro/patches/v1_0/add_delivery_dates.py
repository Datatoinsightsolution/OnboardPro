import frappe

# Creation date + a priority-implied lead time, so legacy rows read plausibly rather than
# as "expected the day it was raised". Display only: every dashboard bucket keys off
# delivery_date (which stays NULL for legacy rows), so this cannot skew any metric.
LEAD_DAYS = {"Urgent": 2, "High": 5, "Medium": 10, "Low": 15}
DEFAULT_LEAD = 7

TABLE = "`tabImplementation Request`"


def execute():
	"""Backfill the new date fields on pre-existing Implementation Requests.

	`expected_date` is `reqd`, and Frappe re-runs mandatory validation on every save,
	not just on insert (frappe/model/document.py:821). The column itself stays nullable
	(`reqd` is not `not_nullable`), so migrate leaves legacy rows at NULL and every
	future save of those rows would raise MandatoryError. Populate them here.
	"""
	if "expected_date" not in frappe.db.get_table_columns("Implementation Request"):
		return  # DocType not synced yet (fresh install) — no legacy rows to fix

	_backfill_expected_date()
	_backfill_resolved_on()
	# delivery_date / delivery_committed_on: nothing to backfill — there is no prior
	# notion of a customer commitment. Legacy rows read "Awaiting commitment".

	frappe.db.commit()


def _backfill_expected_date():
	"""Raw UPDATE, not doc.save(): avoids re-validating every legacy doc, avoids
	writing a Version, and avoids bumping `modified`."""
	for priority, days in LEAD_DAYS.items():
		frappe.db.sql(
			f"""UPDATE {TABLE}
				SET expected_date = DATE_ADD(DATE(creation), INTERVAL %(days)s DAY)
				WHERE expected_date IS NULL AND priority = %(priority)s""",
			{"days": days, "priority": priority},
		)

	frappe.db.sql(
		f"""UPDATE {TABLE}
			SET expected_date = DATE_ADD(DATE(creation), INTERVAL %(days)s DAY)
			WHERE expected_date IS NULL""",
		{"days": DEFAULT_LEAD},
	)


def _backfill_resolved_on():
	"""Recover the real resolution time from Version history.

	track_changes has been on since day one, so this is genuine data rather than a
	fabricated timestamp. set_value with update_modified=False writes below the
	document layer, so it doesn't trip mandatory validation.
	"""
	for name in frappe.get_all(
		"Implementation Request",
		filters={"status": "Resolved", "resolved_on": ["is", "not set"]},
		pluck="name",
	):
		frappe.db.set_value(
			"Implementation Request",
			name,
			"resolved_on",
			_last_resolution_time(name),
			update_modified=False,
		)


def _last_resolution_time(docname):
	"""Newest Version entry that moved status → Resolved; falls back to `modified`."""
	for v in frappe.get_all(
		"Version",
		filters={"ref_doctype": "Implementation Request", "docname": docname},
		fields=["creation", "data"],
		order_by="creation desc",
	):
		try:
			changed = frappe.parse_json(v.data).get("changed", [])
		except Exception:
			continue
		if any(field == "status" and new_val == "Resolved" for field, _old, new_val in changed):
			return v.creation

	return frappe.db.get_value("Implementation Request", docname, "modified")
