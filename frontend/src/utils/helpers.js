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
 * Format a date-only 'YYYY-MM-DD' string.
 * Deliberately NOT fmtDate(toMs(s)): new Date('2026-08-12') parses as UTC midnight, so
 * toLocaleDateString() renders the 11th anywhere west of Greenwich. Splitting the string
 * and building a local-midnight Date keeps the calendar day intact.
 */
export function fmtDay(s) {
	if (!s) return '—'
	const [y, m, d] = String(s).slice(0, 10).split('-').map(Number)
	return new Date(y, m - 1, d).toLocaleDateString(undefined, {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
	})
}

/** Local-calendar 'YYYY-MM-DD'. Never toISOString() — that shifts by the UTC offset. */
export function dateKey(d = new Date()) {
	const p = (n) => String(n).padStart(2, '0')
	return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

/** Whole days from `a` to `b`, both 'YYYY-MM-DD'. */
export function dayDiff(b, a) {
	const t = (s) => {
		const [y, m, d] = String(s).slice(0, 10).split('-').map(Number)
		return Date.UTC(y, m - 1, d)
	}
	return Math.round((t(b) - t(a)) / D)
}

/**
 * Bucket a request against its committed delivery date.
 * Mirrors _delivery_state() in onboardpro/api.py — keep the two in sync.
 *
 * Comparisons are lexicographic on 'YYYY-MM-DD', which is both correct and immune to
 * the timezone shifts that Date-object comparison would introduce.
 */
export function deliveryState(r, today) {
	if (!r?.delivery_date) {
		// Resolved without a commitment (legacy rows) is settled, not a red flag.
		if (r?.status === 'Resolved') return 'awaiting'
		// Past the date staff needed the data by, and still no commitment.
		const exp = r?.expected_date ? String(r.expected_date).slice(0, 10) : null
		return exp && today > exp ? 'nocommit' : 'awaiting'
	}
	const due = String(r.delivery_date).slice(0, 10)
	if (r.status === 'Resolved') {
		const done = String(r.resolved_on || today).slice(0, 10)
		return done > due ? 'late' : 'ontime'
	}
	return today > due ? 'overdue' : 'ontrack'
}

/**
 * Open states that need chasing. Two different failures: "broke the promise" and
 * "never made one". Mirrors ATTENTION_STATES in onboardpro/api.py.
 */
export const ATTENTION_STATES = ['overdue', 'nocommit']

export const DELIVERY_META = {
	awaiting: { label: 'Awaiting commitment', tone: 'slate', icon: 'help-circle' },
	nocommit: { label: 'No commitment', tone: 'red', icon: 'user-x' },
	ontrack: { label: 'On track', tone: 'blue', icon: 'calendar' },
	overdue: { label: 'Overdue', tone: 'red', icon: 'alert-triangle' },
	late: { label: 'Delivered late', tone: 'amber', icon: 'clock' },
	ontime: { label: 'On time', tone: 'green', icon: 'check-circle' },
}

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
	Urgent: { rank: 0, tone: 'red' },
	High: { rank: 1, tone: 'amber' },
	Medium: { rank: 2, tone: 'blue' },
	Low: { rank: 3, tone: 'slate' },
}

export const DATATYPE_ICON = {
	'Master Data': 'database',
	'Opening Balances': 'bar-chart-2',
	Configuration: 'sliders',
	Reconciliation: 'git-merge',
	Documents: 'file',
}
