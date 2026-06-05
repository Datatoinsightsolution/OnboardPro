<template>
	<div class="pulse">
		<div class="h1" style="margin-bottom: 4px">SLA Pulse</div>
		<div style="color: var(--ink-3); font-size: 13.5px; margin-bottom: 22px">
			{{
				role === 'customer'
					? 'Live status of your open data requests.'
					: 'Live health of every open data request.'
			}}
		</div>

		<!-- Stat cards -->
		<div class="stat-grid">
			<div class="stat">
				<div class="lbl"><FeatherIcon name="inbox" />Open requests</div>
				<div class="num">{{ openReqs.length }}</div>
				<div class="sub2">
					{{ role === 'customer' ? 'Your active requests' : 'Across all customers' }}
				</div>
			</div>
			<div class="stat" :data-tone="breached.length ? 'red' : 'green'">
				<div class="lbl"><FeatherIcon name="alert-triangle" />SLA breached</div>
				<div class="num" :style="breached.length ? 'color:var(--t-ink)' : ''">
					{{ breached.length }}
				</div>
				<div class="sub2">Need attention now</div>
			</div>
			<div class="stat" :data-tone="atRisk.length ? 'amber' : 'green'">
				<div class="lbl"><FeatherIcon name="clock" />At risk (&lt;8h)</div>
				<div class="num" :style="atRisk.length ? 'color:var(--t-ink)' : ''">
					{{ atRisk.length }}
				</div>
				<div class="sub2">Approaching deadline</div>
			</div>
			<div class="stat" data-tone="green">
				<div class="lbl"><FeatherIcon name="check-circle" />Resolved</div>
				<div class="num" style="color: var(--t-ink)">{{ resolved.length }}</div>
				<div class="sub2">Data accepted</div>
			</div>
		</div>

		<!-- Watchlist -->
		<div class="section-label">Watchlist · soonest deadlines</div>
		<div class="tablewrap" style="padding: 0 0 40px">
			<table class="tbl">
				<thead>
					<tr>
						<th style="width: 80px">ID</th>
						<th>Request</th>
						<th v-if="role === 'staff'" style="width: 190px">Customer</th>
						<th style="width: 160px">Resolution SLA</th>
						<th style="width: 150px">Status</th>
					</tr>
				</thead>
				<tbody>
					<tr v-if="!watchlist.length">
						<td
							:colspan="role === 'staff' ? 5 : 4"
							style="text-align: center; color: var(--ink-4); height: 80px"
						>
							All clear — nothing at risk.
						</td>
					</tr>
					<tr
						v-for="r in watchlist"
						:key="r.name"
						@click="$router.push({ name: 'RequestDetail', params: { id: r.name } })"
					>
						<td>
							<span class="id">{{ r.name }}</span>
						</td>
						<td>
							<div class="subj">{{ r.subject }}</div>
						</td>
						<td v-if="role === 'staff'">
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
						<td>
							<SlaChip
								:deadline="r.res_due_at"
								:now="now"
								:window-h="PRIORITY_META[r.priority]?.resH ?? 48"
								:state="r.res_state"
							/>
						</td>
						<td><StatusBadge :status="r.status" /></td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { createListResource, FeatherIcon } from 'frappe-ui'
import { toMs, PRIORITY_META } from '@/utils/helpers'
import StatusBadge from '@/components/StatusBadge.vue'
import SlaChip from '@/components/SlaChip.vue'
import RistoAvatar from '@/components/RistoAvatar.vue'

const props = defineProps({ role: { type: String, default: 'staff' } })
const role = computed(() => props.role)

const now = ref(Date.now())
const timer = setInterval(() => {
	now.value = Date.now()
}, 1000)
onUnmounted(() => clearInterval(timer))

const requests = createListResource({
	doctype: 'Implementation Request',
	fields: [
		'name',
		'subject',
		'customer',
		'customer_name',
		'status',
		'priority',
		'res_state',
		'res_due_at',
	],
	orderBy: 'res_due_at asc',
	pageLength: 200,
	auto: true,
})

const all = computed(() => requests.data ?? [])
const openReqs = computed(() => all.value.filter((r) => r.status !== 'Resolved'))
const resolved = computed(() => all.value.filter((r) => r.status === 'Resolved'))
const breached = computed(() => openReqs.value.filter((r) => toMs(r.res_due_at) < now.value))
const atRisk = computed(() =>
	openReqs.value.filter((r) => {
		const ms = toMs(r.res_due_at) - now.value
		return ms > 0 && ms < 8 * 3_600_000
	})
)

const watchlist = computed(() =>
	[...breached.value, ...atRisk.value]
		.sort((a, b) => toMs(a.res_due_at) - toMs(b.res_due_at))
		.slice(0, 8)
)
</script>
