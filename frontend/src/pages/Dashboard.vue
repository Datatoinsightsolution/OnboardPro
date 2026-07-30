<template>
	<div class="dash">
		<div class="h1" style="margin-bottom: 4px">Dashboard</div>
		<div style="color: var(--ink-3); font-size: 13.5px; margin-bottom: 22px">
			{{
				role === 'customer'
					? 'How your data requests are tracking against the dates you committed to.'
					: 'Delivery commitment health across every request.'
			}}
		</div>

		<!-- Loading -->
		<div v-if="data.loading && !data.data" style="text-align: center; padding: 80px 20px">
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

		<template v-else-if="d">
			<!-- Stat cards -->
			<div class="stat-grid">
				<div class="stat">
					<div class="lbl"><FeatherIcon name="inbox" />Open requests</div>
					<div class="num">{{ d.open }}</div>
					<div class="sub2">
						{{ role === 'customer' ? 'Your active requests' : 'Across all customers' }}
					</div>
				</div>

				<div class="stat" :data-tone="c.overdue ? 'red' : 'green'">
					<div class="lbl"><FeatherIcon name="alert-triangle" />Overdue</div>
					<div class="num" :style="c.overdue ? 'color:var(--t-ink)' : ''">
						{{ c.overdue }}
					</div>
					<div class="sub2">Past the committed date</div>
				</div>

				<div class="stat" :data-tone="c.nocommit ? 'red' : 'green'">
					<div class="lbl"><FeatherIcon name="user-x" />No commitment</div>
					<div class="num" :style="c.nocommit ? 'color:var(--t-ink)' : ''">
						{{ c.nocommit }}
					</div>
					<div class="sub2">Past the expected date, no date given</div>
				</div>

				<div class="stat" :data-tone="c.awaiting ? 'amber' : 'slate'">
					<div class="lbl"><FeatherIcon name="help-circle" />Awaiting commitment</div>
					<div class="num" :style="c.awaiting ? 'color:var(--t-ink)' : ''">
						{{ c.awaiting }}
					</div>
					<div class="sub2">
						{{
							d.avg_commitment_slip !== null
								? `Committed dates run ${d.avg_commitment_slip > 0 ? '+' : ''}${
										d.avg_commitment_slip
								  }d vs expected`
								: 'Still within the expected date'
						}}
					</div>
				</div>

				<div class="stat" :data-tone="c.late ? 'amber' : 'green'">
					<div class="lbl"><FeatherIcon name="clock" />Delivered late</div>
					<div class="num" :style="c.late ? 'color:var(--t-ink)' : ''">{{ c.late }}</div>
					<div class="sub2">Resolved after the committed date</div>
				</div>

				<div class="stat" data-tone="green">
					<div class="lbl"><FeatherIcon name="check-circle" />On-time rate</div>
					<div class="num" style="color: var(--t-ink)">
						{{ d.on_time_rate === null ? '—' : d.on_time_rate + '%' }}
					</div>
					<div class="sub2">
						{{
							d.on_time_rate === null
								? 'Nothing delivered yet'
								: `${c.ontime} of ${c.ontime + c.late} delivered on time`
						}}
					</div>
				</div>
			</div>

			<!-- Watchlist -->
			<div class="section-label">Watchlist · overdue first, then soonest due</div>
			<div class="tablewrap" style="padding: 0 0 40px">
				<table class="tbl">
					<thead>
						<tr>
							<th style="width: 80px">ID</th>
							<th>Request</th>
							<th v-if="role === 'staff'" style="width: 190px">Customer</th>
							<th style="width: 120px">Expected</th>
							<th style="width: 175px">Delivery</th>
							<th style="width: 140px">Status</th>
						</tr>
					</thead>
					<tbody>
						<tr v-if="!d.watchlist.length">
							<td
								:colspan="role === 'staff' ? 6 : 5"
								style="text-align: center; color: var(--ink-4); height: 80px"
							>
								All clear — nothing outstanding.
							</td>
						</tr>
						<tr
							v-for="r in d.watchlist"
							:key="r.name"
							@click="
								$router.push({ name: 'RequestDetail', params: { id: r.name } })
							"
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
							<td>{{ fmtDay(r.expected_date) }}</td>
							<td><DeliveryChip :request="r" :today="d.today" /></td>
							<td><StatusBadge :status="r.status" /></td>
						</tr>
					</tbody>
				</table>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource, FeatherIcon } from 'frappe-ui'
import { fmtDay } from '@/utils/helpers'
import StatusBadge from '@/components/StatusBadge.vue'
import DeliveryChip from '@/components/DeliveryChip.vue'
import RistoAvatar from '@/components/RistoAvatar.vue'

const props = defineProps({ role: { type: String, default: 'staff' } })
const emit = defineEmits(['requests-loaded'])
const role = computed(() => props.role)

// One server call. No role branch here — get_dashboard delegates the row-level split to
// the permission_query_conditions hook, so staff and customers hit the same endpoint.
const data = createResource({ url: 'onboardpro.api.get_dashboard', auto: true })

const d = computed(() => data.data)
const c = computed(() => d.value?.counts ?? {})

// Keep the sidebar badges right when the dashboard is the entry view.
watch(d, (v) => {
	if (v) emit('requests-loaded', { open: v.open, overdue: v.attention })
})
</script>
