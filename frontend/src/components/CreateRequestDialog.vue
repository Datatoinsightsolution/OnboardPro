<template>
	<teleport to="body">
		<div class="scrim" @click="$emit('close')"></div>
		<div class="slideover" role="dialog" aria-modal="true">
			<div class="so-head">
				<div>
					<div class="t">New data request</div>
					<div class="s">
						Raise a request against a customer to collect implementation data
					</div>
				</div>
				<button class="iconbtn" @click="$emit('close')">
					<FeatherIcon name="x" />
				</button>
			</div>

			<div class="so-body">
				<!-- Subject -->
				<div>
					<div
						style="
							display: flex;
							align-items: baseline;
							justify-content: space-between;
							margin-bottom: 5px;
						"
					>
						<label class="flabel" style="margin-bottom: 0"
							>Subject
							<span data-tone="red" style="color: var(--t-ink)">*</span></label
						>
						<span
							style="font-size: 11px"
							:style="{
								color:
									form.subject.length > 120
										? 'oklch(0.50 0.18 25)'
										: 'var(--ink-4)',
							}"
						>
							{{ form.subject.length }}/140
						</span>
					</div>
					<input
						v-model="form.subject"
						class="finput"
						autofocus
						maxlength="140"
						placeholder="e.g. Provide opening balances — FY25"
					/>
					<div
						v-if="form.subject.length > 120"
						style="font-size: 12px; color: oklch(0.5 0.18 25); margin-top: 4px"
					>
						{{ 140 - form.subject.length }} characters remaining — keep subjects
						concise.
					</div>
				</div>

				<!-- Customer — searchable select (scales to many customers) -->
				<div>
					<label class="flabel">Customer</label>
					<select v-model="form.customer" class="finput">
						<option value="" disabled>Select customer…</option>
						<option v-for="c in customers.data ?? []" :key="c.name" :value="c.name">
							{{ c.customer_name || c.name }}
						</option>
					</select>
				</div>

				<!-- Expected date -->
				<div>
					<label class="flabel">
						Expected date
						<span data-tone="red" style="color: var(--t-ink)">*</span>
					</label>
					<input
						v-model="form.expected_date"
						type="date"
						class="finput"
						:min="todayStr"
					/>
					<div class="fhint">
						When you need this data by. The customer commits to their own delivery date
						after seeing the request.
					</div>
				</div>

				<!-- Data type -->
				<div>
					<label class="flabel">Data type</label>
					<div class="chiprow">
						<button
							v-for="dt in DATA_TYPES"
							:key="dt"
							type="button"
							:class="['chip', form.data_type === dt ? 'on' : '']"
							@click="form.data_type = dt"
						>
							<FeatherIcon
								:name="DATATYPE_ICON[dt]"
								style="width: 15px; height: 15px"
							/>
							{{ dt }}
						</button>
					</div>
				</div>

				<!-- Priority -->
				<div>
					<label class="flabel">Priority</label>
					<div class="chiprow">
						<button
							v-for="(meta, p) in PRIORITY_META"
							:key="p"
							type="button"
							:class="['chip', form.priority === p ? 'on' : '']"
							:data-tone="meta.tone"
							@click="form.priority = p"
						>
							<span class="dot"></span>{{ p }}
						</button>
					</div>
				</div>

				<!-- Instructions -->
				<div>
					<label class="flabel">Instructions to customer</label>
					<textarea
						v-model="form.description"
						class="finput fta"
						placeholder="Describe exactly what data is needed, format, cut-off dates…"
					/>
					<div class="fhint">
						The customer sees this in the request, along with any template you attach
						after creating it.
					</div>
				</div>
			</div>

			<div class="so-foot">
				<span class="grow" style="font-size: 12px; color: var(--ink-3)"
					>Assigned to you · {{ currentUserName }}</span
				>
				<button class="btn" @click="$emit('close')">Cancel</button>
				<button class="btn primary" :disabled="!isValid || submitting" @click="submit">
					<FeatherIcon name="plus" style="width: 14px; height: 14px" />
					{{ submitting ? 'Raising…' : 'Raise request' }}
				</button>
			</div>
		</div>
	</teleport>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { createResource, FeatherIcon } from 'frappe-ui'
import { PRIORITY_META, DATATYPE_ICON, dateKey } from '@/utils/helpers'

const emit = defineEmits(['close', 'created'])
const toast = inject('toast', () => {})

const currentUserName = window.frappe?.session?.user_fullname || 'Staff'

const DATA_TYPES = [
	'Master Data',
	'Opening Balances',
	'Configuration',
	'Reconciliation',
	'Documents',
]

// Deliberately no default expected date — the whole feature rests on this being a real
// deadline, and a pre-filled value invites nobody to think about it.
const form = ref({
	subject: '',
	customer: '',
	expected_date: '',
	data_type: 'Master Data',
	priority: 'High',
	description: '',
})
const submitting = ref(false)
const todayStr = dateKey()

// Load customers via whitelisted API to avoid permission issues
const customers = createResource({
	url: 'onboardpro.api.search_customers',
	params: { query: '', limit: 500 },
	auto: true,
})

const isValid = computed(
	() =>
		form.value.subject.trim().length > 2 && !!form.value.customer && !!form.value.expected_date
)

const insertDoc = createResource({
	url: 'frappe.client.insert',
	onSuccess(doc) {
		submitting.value = false
		toast('Request ' + doc.name + ' raised')
		emit('created', doc.name)
	},
	onError() {
		submitting.value = false
	},
})

function submit() {
	if (!isValid.value) return
	submitting.value = true
	insertDoc.submit({
		doc: {
			doctype: 'Implementation Request',
			subject: form.value.subject.trim(),
			customer: form.value.customer,
			expected_date: form.value.expected_date,
			data_type: form.value.data_type,
			priority: form.value.priority,
			description: form.value.description.trim(),
			status: 'Open',
		},
	})
}
</script>
