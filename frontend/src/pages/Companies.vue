<template>
	<div v-if="role !== 'staff'" class="empty">
		<FeatherIcon name="lock" />
		<div style="font-weight: 600; color: var(--ink-2)">Not permitted</div>
		<div style="font-size: 13px">Only OnboardPro staff can manage companies.</div>
	</div>

	<div v-else>
		<div class="subhead">
			<div class="h1">Companies</div>
		</div>

		<div class="toolbar">
			<label class="search" style="max-width: 320px">
				<FeatherIcon name="briefcase" />
				<input
					v-model="newCompanyName"
					placeholder="New company name…"
					@keyup.enter="createCompany"
				/>
			</label>
			<button
				class="btn primary"
				:disabled="!newCompanyName.trim() || creating"
				@click="createCompany"
			>
				<FeatherIcon name="plus" style="width: 14px; height: 14px" />
				{{ creating ? 'Adding…' : 'Add company' }}
			</button>
			<div style="flex: 1"></div>
		</div>

		<!-- Loading -->
		<div v-if="hierarchy.loading" style="text-align: center; padding: 80px 20px">
			<div
				style="
					width: 24px;
					height: 24px;
					border: 2px solid var(--accent);
					border-top-color: transparent;
					border-radius: 99px;
					animation: co-spin 0.7s linear infinite;
					margin: 0 auto;
				"
			></div>
		</div>

		<!-- Empty -->
		<div v-else-if="!(hierarchy.data ?? []).length" class="empty">
			<FeatherIcon name="briefcase" />
			<div style="font-weight: 600; color: var(--ink-2)">No companies yet</div>
			<div style="font-size: 13px">Add a company above, then assign customers to it.</div>
		</div>

		<!-- Company tree: Company → Managers / Users -->
		<div v-else class="companies">
			<div v-for="c in hierarchy.data" :key="c.name" class="company-card">
				<div class="company-head">
					<div>
						<FeatherIcon
							name="briefcase"
							style="width: 16px; height: 16px; opacity: 0.6"
						/>
						<span class="company-name">{{ c.company_name }}</span>
					</div>
					<button class="btn sm" @click="assignTarget = c">
						<FeatherIcon name="user-plus" style="width: 13px; height: 13px" />
						Assign
					</button>
				</div>

				<div v-for="group in ['Manager', 'User']" :key="group" class="role-group">
					<div class="role-label">{{ group === 'Manager' ? 'Managers' : 'Users' }}</div>
					<div
						v-if="!membersByRole(c, group).length"
						style="font-size: 12px; color: var(--ink-4); font-style: italic; padding: 4px 0"
					>
						No one assigned
					</div>
					<div v-for="m in membersByRole(c, group)" :key="m.user" class="member-row">
						<RistoAvatar :name="m.customer_name || m.user" role="customer" :size="26" />
						<div class="member-info">
							<div class="nm">{{ m.customer_name }}</div>
							<div class="em">{{ m.user }}</div>
						</div>
						<select
							class="role-sel"
							:value="m.designation"
							@change="changeDesignation(c, m, $event.target.value)"
						>
							<option value="Manager">Manager</option>
							<option value="User">User</option>
						</select>
						<button class="iconbtn" title="Remove from company" @click="removeMember(m)">
							<FeatherIcon name="x" style="width: 14px; height: 14px" />
						</button>
					</div>
				</div>
			</div>
		</div>

		<AssignCustomerDialog
			v-if="assignTarget"
			:company="assignTarget"
			@close="assignTarget = null"
			@assigned="onAssigned"
		/>
	</div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { createResource, FeatherIcon } from 'frappe-ui'
import RistoAvatar from '@/components/RistoAvatar.vue'
import AssignCustomerDialog from '@/components/AssignCustomerDialog.vue'

defineProps({ role: { type: String, default: 'staff' } })

const toast = inject('toast', () => {})

const newCompanyName = ref('')
const creating = ref(false)
const assignTarget = ref(null)

const hierarchy = createResource({
	url: 'onboardpro.api.get_company_hierarchy',
	auto: true,
})

const insertCompany = createResource({
	url: 'frappe.client.insert',
	onSuccess() {
		creating.value = false
		newCompanyName.value = ''
		toast('Company added')
		hierarchy.reload()
	},
	onError() {
		creating.value = false
	},
})

function createCompany() {
	const name = newCompanyName.value.trim()
	if (!name) return
	creating.value = true
	insertCompany.submit({ doc: { doctype: 'Onboardpro Company', company_name: name } })
}

function membersByRole(company, designation) {
	return (company.members ?? []).filter((m) => m.designation === designation)
}

const assignAction = createResource({
	url: 'onboardpro.api.assign_customer',
	onSuccess() {
		hierarchy.reload()
	},
})

function changeDesignation(company, member, designation) {
	assignAction.submit({ user: member.user, company: company.name, designation })
}

function onAssigned() {
	assignTarget.value = null
	toast('Customer assigned')
	hierarchy.reload()
}

const deleteMember = createResource({
	url: 'frappe.client.delete',
	onSuccess() {
		toast('Assignment removed')
		hierarchy.reload()
	},
})

function removeMember(member) {
	deleteMember.submit({ doctype: 'Onboardpro Customer', name: member.user })
}
</script>

<style>
@keyframes co-spin {
	to {
		transform: rotate(360deg);
	}
}

.companies {
	display: flex;
	flex-direction: column;
	gap: 14px;
	padding: 18px 22px 40px;
}

.company-card {
	background: var(--surface);
	border: 1px solid var(--border);
	border-radius: var(--r-lg);
	box-shadow: var(--sh-1);
	padding: 16px 18px;
}

.company-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
	padding-bottom: 12px;
	margin-bottom: 12px;
	border-bottom: 1px solid var(--border);
}

.company-head > div:first-child {
	display: flex;
	align-items: center;
	gap: 8px;
}

.company-name {
	font-weight: 700;
	font-size: 15px;
	letter-spacing: -0.01em;
}

.role-group + .role-group {
	margin-top: 14px;
}

.role-label {
	font-size: 10.5px;
	font-weight: 700;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: var(--ink-4);
	margin-bottom: 6px;
}

.member-row {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 7px 0;
}

.member-row .member-info {
	flex: 1;
	min-width: 0;
}

.member-row .nm {
	font-weight: 550;
	font-size: 13.5px;
}

.member-row .em {
	font-size: 11.5px;
	color: var(--ink-3);
}

.role-sel {
	font-size: 12px;
	border: 1px solid var(--border-2);
	border-radius: var(--r);
	padding: 5px 8px;
	background: var(--surface);
	color: var(--ink);
}
</style>
