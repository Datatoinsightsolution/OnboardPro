export const H = 3_600_000
export const D = 24 * H
export const M = 60_000

/** Convert Frappe ISO date string → ms timestamp */
export const toMs = (s) => (s ? new Date(s).getTime() : 0)

/** Relative "X ago" label */
export function fmtAgo(ms, now) {
	const d = now - ms
	if (d < M) return 'just now'
	if (d < H) return Math.round(d / M) + 'm ago'
	if (d < D) return Math.round(d / H) + 'h ago'
	const days = Math.round(d / D)
	if (days < 7) return days + (days === 1 ? ' day ago' : ' days ago')
	return new Date(ms).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function fmtDate(ms) {
	return new Date(ms).toLocaleDateString(undefined, {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
	})
}

/**
 * SLA countdown. Returns { ms, breached, label, short, tone, pct }
 * tone: "ok" | "warn" | "breach"
 */
export function sla(deadlineMs, now, windowH) {
	const left = deadlineMs - now
	const breached = left <= 0
	const a = Math.abs(left)
	const h = Math.floor(a / H)
	const m = Math.floor((a % H) / M)
	let core
	if (h >= 48) core = Math.round(h / 24) + 'd'
	else if (h >= 1) core = h + 'h ' + String(m).padStart(2, '0') + 'm'
	else core = m + 'm'
	const label = breached ? 'Breached ' + core : core + ' left'
	const short = breached ? '−' + core : core
	let tone = 'ok'
	if (breached) tone = 'breach'
	else if (left < 4 * H) tone = 'warn'
	const pct = windowH ? Math.min(1.4, 1 - left / (windowH * H)) : 0
	return { ms: left, breached, label, short, tone, pct }
}

/** Map SLA tone → CSS data-tone attribute value */
export const SLA_TONE_MAP = { ok: 'green', warn: 'amber', breach: 'red' }

/** Generate 2-letter initials from a full name */
export function initials(name) {
	return (name || '?')
		.split(' ')
		.filter(Boolean)
		.map((w) => w[0])
		.join('')
		.slice(0, 2)
		.toUpperCase()
}

export const STATUS_META = {
	Open: { tone: 'blue', group: 'open', desc: 'Raised — awaiting action' },
	'In Review': { tone: 'violet', group: 'open', desc: 'Risto reviewing submission' },
	'Needs Revision': { tone: 'red', group: 'open', desc: 'Sent back to customer' },
	Resolved: { tone: 'green', group: 'closed', desc: 'Data accepted & complete' },
}

export const PRIORITY_META = {
	Urgent: { rank: 0, tone: 'red', frH: 4, resH: 24 },
	High: { rank: 1, tone: 'amber', frH: 8, resH: 48 },
	Medium: { rank: 2, tone: 'blue', frH: 24, resH: 96 },
	Low: { rank: 3, tone: 'slate', frH: 48, resH: 168 },
}

export const DATATYPE_ICON = {
	'Master Data': 'database',
	'Opening Balances': 'bar-chart-2',
	Configuration: 'sliders',
	Reconciliation: 'git-merge',
	Documents: 'file',
}

export const SLA_STATE_TONE = {
	Fulfilled: 'green',
	Failed: 'red',
	'In Progress': 'blue',
	Paused: 'slate',
}
