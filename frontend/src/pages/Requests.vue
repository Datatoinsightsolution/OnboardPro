<template>
	<div>
		<!-- Tabs + title -->
		<div class="subhead">
			<div class="h1">{{ role === 'customer' ? 'Your data requests' : 'Requests' }}</div>
			<div class="tabs">
				<button
					v-for="tab in TABS"
					:key="tab.key"
					:class="['tab', activeTab === tab.key ? 'on' : '']"
					@click="activeTab = tab.key"
				>
					<FeatherIcon
						v-if="tab.key === 'breached' && counts[tab.key] > 0"
						name="alert-triangle"
						style="width: 13px; height: 13px; color: var(--t-solid)"
						data-tone="red"
					/>
					{{ tab.label }}
					<span class="cnt" :data-tone="tab.key === 'breached' ? 'red' : 'slate'">{{
						counts[tab.key] ?? 0
					}}</span>
				</button>
			</div>
		</div>

		<!-- Toolbar -->
		<div class="toolbar">
			<label class="search">
				<FeatherIcon name="search" />
				<input v-model="q" placeholder="Search by subject, customer, ID…" />
			</label>
			<div style="flex: 1"></div>

			<!-- Sort control -->
			<div class="sort-ctrl">
				<select v-model="sortField" class="sort-sel">
					<option value="creation">Created</option>
					<option value="modified">Last updated</option>
					<option value="priority">Priority</option>
				</select>
				<button
					class="sort-dir"
					:title="sortDir === 'desc' ? 'Descending' : 'Ascending'"
					@click="sortDir = sortDir === 'desc' ? 'asc' : 'desc'"
				>
					<FeatherIcon
						:name="sortDir === 'desc' ? 'arrow-down' : 'arrow-up'"
						style="width: 14px; height: 14px"
					/>
				</button>
			</div>

			<div class="seg-mini">
				<button
					:class="layout === 'table' ? 'on' : ''"
					title="Table"
					@click="layout = 'table'"
				>
					<FeatherIcon name="list" />
				</button>
				<button
					:class="layout === 'cards' ? 'on' : ''"
					title="Cards"
					@click="layout = 'cards'"
				>
					<FeatherIcon name="grid" />
				</button>
				<button
					:class="layout === 'kanban' ? 'on' : ''"
					title="Board"
					@click="layout = 'kanban'"
				>
					<FeatherIcon name="columns" />
				</button>
			</div>
			<button v-if="role === 'staff'" class="btn primary" @click="createOpen = true">
				<FeatherIcon name="plus" style="width: 15px; height: 15px" />New request
			</button>
		</div>

		<!-- Loading -->
		<div v-if="requests.list.loading" style="text-align: center; padding: 80px 20px">
			<div
				style="
					width: 24px;
					height: 24px;
					border: 2px solid var(--accent);
					border-top-color: transparent;
					border-radius: 99px;
					animation: spin 0.7s linear infinite;
					margin: 0 auto;
				"
			></div>
		</div>

		<!-- Empty -->
		<div v-else-if="rows.length === 0" class="empty">
			<FeatherIcon name="inbox" />
			<div style="font-weight: 600; color: var(--ink-2)">Nothing here</div>
			<div style="font-size: 13px">No requests match this filter.</div>
		</div>

		<!-- Table view -->
		<template v-else-if="layout === 'table'">
			<div class="tablewrap">
				<table class="tbl">
					<thead>
						<tr>
							<th style="width: 80px">ID</th>
							<th>Request</th>
							<th style="width: 190px">Customer</th>
							<th style="width: 110px">Priority</th>
							<th style="width: 150px">SLA</th>
							<th style="width: 150px">Status</th>
							<th v-if="role === 'staff'" style="width: 48px">Owner</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="r in rows"
							:key="r.name"
							:class="{ unread: unreadSet.has(r.name) }"
							@click="open(r.name)"
						>
							<td>
								<span class="id">{{ r.name }}</span>
							</td>
							<td class="req-cell" :title="r.subject">
								<div class="subj">{{ r.subject }}</div>
								<div class="meta">
									<FeatherIcon
										:name="DATATYPE_ICON[r.data_type] || 'file'"
										style="width: 13px; height: 13px; opacity: 0.6"
									/>
									{{ r.data_type }}
								</div>
							</td>
							<td>
								<div class="cust-cell">
									<RistoAvatar
										:name="r.customer_name || r.customer"
										role="customer"
										:size="28"
									/>
									<div>
										<div class="nm">{{ r.customer_name }}</div>
										<div class="co">{{ r.customer }}</div>
									</div>
								</div>
							</td>
							<td><PriorityBadge :priority="r.priority" /></td>
							<td>
								<SlaChip
									:deadline="r.res_due_at"
									:now="now"
									:window-h="PRIORITY_META[r.priority]?.resH ?? 48"
									:state="r.res_state"
								/>
							</td>
							<td><StatusBadge :status="r.status" /></td>
							<td v-if="role === 'staff'">
								<RistoAvatar
									:name="r.assignee_name || r.assignee || '?'"
									role="staff"
									:size="28"
								/>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</template>

		<!-- Cards view -->
		<template v-else-if="layout === 'cards'">
			<div class="cards">
				<div
					v-for="r in rows"
					:key="r.name"
					:class="['rcard', unreadSet.has(r.name) ? 'unread' : '']"
					@click="open(r.name)"
				>
					<div class="top">
						<span class="id">#{{ r.name }}</span>
						<StatusBadge :status="r.status" />
					</div>
					<div class="subj">{{ r.subject }}</div>
					<div style="display: flex; align-items: center; gap: 8px">
						<span class="pill" data-tone="slate" style="gap: 6px">
							<FeatherIcon
								:name="DATATYPE_ICON[r.data_type] || 'file'"
								style="width: 12px; height: 12px"
							/>
							{{ r.data_type }}
						</span>
						<PriorityBadge :priority="r.priority" />
					</div>
					<div style="margin-top: auto">
						<SlaChip
							:deadline="r.res_due_at"
							:now="now"
							:window-h="PRIORITY_META[r.priority]?.resH ?? 48"
							:state="r.res_state"
						/>
					</div>
					<div class="foot">
						<div class="cust-cell">
							<RistoAvatar
								:name="r.customer_name || r.customer"
								role="customer"
								:size="20"
							/>
							<span class="co" style="font-weight: 550; color: var(--ink-2)">{{
								r.customer_name
							}}</span>
						</div>
					</div>
				</div>
			</div>
		</template>

		<!-- Kanban view -->
		<template v-else>
			<div style="overflow-x: auto">
				<div class="board">
					<div v-for="col in BOARD_COLS" :key="col" class="col">
						<div class="col-head">
							<StatusBadge :status="col" />
							<span class="cnt">{{ byCol[col]?.length ?? 0 }}</span>
						</div>
						<div class="col-body">
							<div
								v-for="r in byCol[col]"
								:key="r.name"
								:class="['kcard', unreadSet.has(r.name) ? 'unread' : '']"
								@click="open(r.name)"
							>
								<div class="row">
									<span
										style="
											font-family: var(--mono);
											font-size: 11px;
											color: var(--ink-4);
										"
										>#{{ r.name }}</span
									>
									<PriorityBadge :priority="r.priority" />
								</div>
								<div class="subj">{{ r.subject }}</div>
								<div class="row">
									<SlaChip
										:deadline="r.res_due_at"
										:now="now"
										:window-h="PRIORITY_META[r.priority]?.resH ?? 48"
										:state="r.res_state"
									/>
								</div>
								<div
									class="row"
									style="padding-top: 8px; border-top: 1px solid var(--border)"
								>
									<div class="cust-cell">
										<RistoAvatar
											:name="r.customer_name || r.customer"
											role="customer"
											:size="20"
										/>
										<span class="co">{{ r.customer_name }}</span>
									</div>
									<RistoAvatar
										:name="r.assignee_name || r.assignee || '?'"
										role="staff"
										:size="20"
									/>
								</div>
							</div>
							<div
								v-if="!byCol[col]?.length"
								style="
									font-size: 12px;
									color: var(--ink-4);
									padding: 10px 4px;
									font-style: italic;
								"
							>
								No requests
							</div>
						</div>
					</div>
				</div>
			</div>
		</template>

		<CreateRequestDialog v-if="createOpen" @close="createOpen = false" @created="onCreated" />
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { createListResource, FeatherIcon, frappeRequest } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { PRIORITY_META, DATATYPE_ICON, toMs } from '@/utils/helpers'
import StatusBadge from '@/components/StatusBadge.vue'
import PriorityBadge from '@/components/PriorityBadge.vue'
import SlaChip from '@/components/SlaChip.vue'
import RistoAvatar from '@/components/RistoAvatar.vue'
import CreateRequestDialog from '@/components/CreateRequestDialog.vue'

const props = defineProps({ role: { type: String, default: 'staff' } })
const emit = defineEmits(['requests-loaded'])
const router = useRouter()

const activeTab = ref('all')
const layout = ref('table')
const q = ref('')
const createOpen = ref(false)
const now = ref(Date.now())
const unreadSet = ref(new Set())
const sortField = ref('creation')
const sortDir = ref('desc')

async function refreshUnread() {
	if (props.role !== 'staff') return
	const result = await frappeRequest({ url: 'onboardpro.api.get_unread_requests' })
	unreadSet.value = new Set(result)
}

onMounted(refreshUnread)

const timer = setInterval(() => {
	now.value = Date.now()
}, 1000)
onUnmounted(() => clearInterval(timer))

const TABS = [
	{ key: 'all', label: 'All' },
	{ key: 'In Review', label: 'In Review' },
	{ key: 'Needs Revision', label: 'Needs Revision' },
	{ key: 'Resolved', label: 'Resolved' },
	{ key: 'breached', label: 'Breached' },
]

const BOARD_COLS = ['Open', 'In Review', 'Needs Revision', 'Resolved']

const requests = createListResource({
	doctype: 'Implementation Request',
	fields: [
		'name',
		'subject',
		'customer',
		'customer_name',
		'status',
		'priority',
		'data_type',
		'assignee',
		'assignee_name',
		'fr_state',
		'res_state',
		'fr_due_at',
		'res_due_at',
		'creation',
		'modified',
	],
	orderBy: 'creation desc',
	pageLength: 100,
	auto: true,
})

const all = computed(() => requests.data ?? [])

function matchTab(r, tab) {
	if (tab === 'all') return true
	if (tab === 'breached') return r.status !== 'Resolved' && toMs(r.res_due_at) < now.value
	return r.status === tab
}

const filtered = computed(() => {
	let rs = all.value
	if (q.value.trim()) {
		const s = q.value.toLowerCase()
		rs = rs.filter((r) =>
			(r.subject + r.customer_name + r.name + r.data_type).toLowerCase().includes(s)
		)
	}
	return rs
})

const sorted = computed(() => {
	const dir = sortDir.value === 'asc' ? 1 : -1
	const field = sortField.value
	return [...filtered.value].sort((a, b) => {
		const va = field === 'priority' ? PRIORITY_META[a.priority]?.rank ?? 99 : a[field] ?? ''
		const vb = field === 'priority' ? PRIORITY_META[b.priority]?.rank ?? 99 : b[field] ?? ''
		return va < vb ? -dir : va > vb ? dir : 0
	})
})

const rows = computed(() => sorted.value.filter((r) => matchTab(r, activeTab.value)))

const counts = computed(() => {
	const rs = filtered.value
	const c = { all: rs.length }
	TABS.slice(1).forEach((t) => {
		c[t.key] = rs.filter((r) => matchTab(r, t.key)).length
	})
	return c
})

const byCol = computed(() => {
	const m = {}
	BOARD_COLS.forEach((c) => {
		m[c] = []
	})
	sorted.value.forEach((r) => {
		if (m[r.status]) m[r.status].push(r)
	})
	return m
})

watch(
	all,
	(rs) => {
		const open = rs.filter((r) => r.status !== 'Resolved').length
		const breach = rs.filter(
			(r) => r.status !== 'Resolved' && toMs(r.res_due_at) < now.value
		).length
		emit('requests-loaded', { open, breach })
	},
	{ immediate: true }
)

function open(id) {
	router.push({ name: 'RequestDetail', params: { id } })
}
function onCreated(id) {
	createOpen.value = false
	requests.reload()
	refreshUnread()
	open(id)
}
</script>

<style>
@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
</style>
