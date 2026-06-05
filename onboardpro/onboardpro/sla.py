"""
Working-hours-aware SLA engine for OnboardPro Implementation Requests.

Architecture mirrors Frappe Helpdesk's HD Service Level Agreement:
  - Deadlines skip non-working hours, weekends, and holidays
  - Resolution clock pauses when request is in "Awaiting Data" status
  - Accumulated hold time extends the resolution deadline
  - First response is stamped when staff sends the first reply
  - An hourly scheduled job back-fills breach states
"""

from datetime import date as _date
from datetime import datetime as _datetime
from datetime import time as _time
from datetime import timedelta

import frappe
from frappe.utils import get_datetime, getdate, now_datetime

# Status where the resolution clock is paused (staff is actively reviewing)
PAUSED_STATUSES = {"In Review"}
RESOLVED_STATUSES = {"Resolved"}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _secs(t):
	"""Convert a Frappe Time field (timedelta or 'HH:MM:SS' string) to seconds from midnight."""
	if t is None:
		return 0
	if hasattr(t, "total_seconds"):
		return int(t.total_seconds())
	if isinstance(t, str):
		h, m, s = t.split(":")
		return int(h) * 3600 + int(m) * 60 + int(float(s))
	return 0


def _workdays(policy):
	"""Return {weekday_name: {"start": secs, "end": secs}} from policy.working_hours."""
	return {
		row.workday: {"start": _secs(row.start_time), "end": _secs(row.end_time)}
		for row in policy.working_hours
	}


def _holidays(policy):
	"""Return a set of date objects from policy.holidays."""
	return {getdate(row.holiday_date) for row in policy.holidays if row.holiday_date}


def _priority_conf(policy, priority):
	"""Return the SLA Priority row matching the given priority name, or None."""
	for row in policy.priorities:
		if row.priority == priority:
			return row
	return None


# ── Core deadline calculation ─────────────────────────────────────────────────


def calc_deadline(start_at, hours, workdays, holidays, hold_seconds=0):
	"""
	Walk forward from start_at consuming only working-hour seconds until
	`hours * 3600 + hold_seconds` have been spent.

	:param start_at: Start datetime (string or datetime object)
	:param hours: SLA window in hours (int or float)
	:param workdays: dict from _workdays()
	:param holidays: set of date objects from _holidays()
	:param hold_seconds: extra seconds added to the target (hold-time extension)
	:return: deadline as Python datetime
	"""
	remaining = int(hours * 3600) + int(hold_seconds)
	result = get_datetime(start_at)
	if not isinstance(result, _datetime):
		result = _datetime.fromisoformat(str(result))

	safety = 0
	while remaining > 0 and safety < 730:
		safety += 1
		cur_date = result.date()
		weekday = cur_date.strftime("%A")

		if cur_date in holidays or weekday not in workdays:
			result = _datetime.combine(cur_date + timedelta(days=1), _time(0, 0))
			continue

		wd = workdays[weekday]
		ws, we = wd["start"], wd["end"]
		cur_secs = result.hour * 3600 + result.minute * 60 + result.second

		if cur_secs < ws:
			result = _datetime.combine(cur_date, _time(0, 0)) + timedelta(seconds=ws)
			cur_secs = ws

		if cur_secs >= we:
			result = _datetime.combine(cur_date + timedelta(days=1), _time(0, 0))
			continue

		available = we - cur_secs
		take = min(remaining, available)
		remaining -= take
		result = result + timedelta(seconds=take)

	return result


def calc_elapsed_time(start, end, workdays, holidays):
	"""
	Measure actual working seconds between start and end,
	excluding non-working hours, weekends, and holidays.
	"""
	start = get_datetime(start)
	end = get_datetime(end)
	if not isinstance(start, _datetime):
		start = _datetime.fromisoformat(str(start))
	if not isinstance(end, _datetime):
		end = _datetime.fromisoformat(str(end))

	if start >= end:
		return 0

	total = 0
	cur_date = start.date()
	end_date = end.date()

	while cur_date <= end_date:
		weekday = cur_date.strftime("%A")
		if cur_date in holidays or weekday not in workdays:
			cur_date += timedelta(days=1)
			continue

		wd = workdays[weekday]
		ws, we = wd["start"], wd["end"]

		eff_start = (
			max(start.hour * 3600 + start.minute * 60 + start.second, ws) if cur_date == start.date() else ws
		)
		eff_end = min(end.hour * 3600 + end.minute * 60 + end.second, we) if cur_date == end_date else we

		if eff_start < eff_end:
			total += eff_end - eff_start

		cur_date += timedelta(days=1)

	return total


# ── Deadline setter ───────────────────────────────────────────────────────────


def _set_deadlines(doc, policy, wdays, hdays):
	"""Recalculate fr_due_at and res_due_at using business hours."""
	pconf = _priority_conf(policy, doc.priority)
	if not pconf:
		return

	creation = get_datetime(doc.sla_creation or now_datetime())
	hold = doc.total_hold_time or 0

	doc.fr_due_at = calc_deadline(creation, pconf.response_time, wdays, hdays)
	doc.res_due_at = calc_deadline(creation, pconf.resolution_time, wdays, hdays, hold_seconds=hold)


# ── Main entry point ──────────────────────────────────────────────────────────


def apply_sla(doc):
	"""
	Called from ImplementationRequest.before_insert and validate.
	Handles: policy binding, deadline calculation, pause/resume, SLA state.
	"""
	# Resolve policy
	policy_name = doc.sla_policy or (
		frappe.db.get_value("SLA Policy", {"is_default": 1, "enabled": 1}, "name")
		or frappe.db.get_value("SLA Policy", {"enabled": 1}, "name")
	)
	if not policy_name:
		return

	policy = frappe.get_doc("SLA Policy", policy_name)
	doc.sla_policy = policy.name
	wdays = _workdays(policy)
	hdays = _holidays(policy)

	# ── New document ──────────────────────────────────────────────────────────
	if doc.is_new():
		doc.sla_creation = now_datetime()
		doc.fr_state = "In Progress"
		doc.res_state = "In Progress"
		_set_deadlines(doc, policy, wdays, hdays)
		return

	# ── Existing document — handle status change ───────────────────────────────
	old = doc.get_doc_before_save()
	old_status = old.status if old else doc.status
	new_status = doc.status

	if old_status != new_status:
		_handle_status_change(doc, policy, wdays, hdays, old_status, new_status)

	# Recalculate deadlines if priority changed
	if doc.has_value_changed("priority"):
		_set_deadlines(doc, policy, wdays, hdays)


def _handle_status_change(doc, policy, wdays, hdays, old_status, new_status):
	"""Manage pause/resume, first-response stamp, and resolution SLA on status transition."""
	now = now_datetime()
	was_paused = old_status in PAUSED_STATUSES
	is_paused = new_status in PAUSED_STATUSES
	is_resolved = new_status in RESOLVED_STATUSES

	# ── Entering pause ────────────────────────────────────────────────────────
	if is_paused and not was_paused:
		doc.on_hold_since = now

	# ── Leaving pause → accumulate hold time, extend resolution deadline ──────
	elif was_paused and not is_paused and doc.on_hold_since:
		elapsed = calc_elapsed_time(doc.on_hold_since, now, wdays, hdays)
		doc.total_hold_time = (doc.total_hold_time or 0) + elapsed
		doc.on_hold_since = None
		_set_deadlines(doc, policy, wdays, hdays)

	# ── Resolution ────────────────────────────────────────────────────────────
	if is_resolved and doc.res_state == "In Progress":
		res_due = get_datetime(doc.res_due_at) if doc.res_due_at else None
		doc.res_state = "Fulfilled" if (res_due and get_datetime(now) <= res_due) else "Failed"

	# ── Reopened from Resolved ────────────────────────────────────────────────
	if old_status in RESOLVED_STATUSES and new_status not in RESOLVED_STATUSES:
		doc.res_state = "In Progress"


# ── First-response stamping (from add_comment) ────────────────────────────────


def set_first_response(docname):
	"""
	Stamp first_responded_on when a staff member sends the first comment.
	Called from api.add_comment after confirming the commenter is staff.
	"""
	values = frappe.db.get_value(
		"Implementation Request",
		docname,
		["first_responded_on", "fr_state", "fr_due_at"],
		as_dict=True,
	)
	if not values or values.first_responded_on or values.fr_state != "In Progress":
		return

	now = now_datetime()
	fr_due = get_datetime(values.fr_due_at) if values.fr_due_at else None
	fr_state = "Fulfilled" if (fr_due and get_datetime(now) <= fr_due) else "Failed"

	frappe.db.set_value(
		"Implementation Request",
		docname,
		{"first_responded_on": now, "fr_state": fr_state},
		update_modified=False,
	)
	frappe.db.commit()


# ── Scheduled job ─────────────────────────────────────────────────────────────


def update_all_sla_statuses():
	"""
	Hourly scheduled job.
	Back-fills fr_state/res_state = 'Failed' for requests that silently breached
	without a save event (e.g. no one touched the request since creation).
	"""
	open_reqs = frappe.get_all(
		"Implementation Request",
		filters={
			"status": ["not in", list(RESOLVED_STATUSES)],
			"sla_policy": ["is", "set"],
			"on_hold_since": ["is", "not set"],
		},
		fields=["name", "fr_state", "res_state", "fr_due_at", "res_due_at"],
	)

	now = now_datetime()
	for req in open_reqs:
		updates = {}

		if req.fr_state == "In Progress" and req.fr_due_at:
			if get_datetime(req.fr_due_at) < now:
				updates["fr_state"] = "Failed"

		if req.res_state == "In Progress" and req.res_due_at:
			if get_datetime(req.res_due_at) < now:
				updates["res_state"] = "Failed"

		if updates:
			frappe.db.set_value("Implementation Request", req.name, updates, update_modified=False)

	if open_reqs:
		frappe.db.commit()
