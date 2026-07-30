<template>
	<teleport to="body">
		<div class="scrim" @click="$emit('close')"></div>
		<div class="slideover" role="dialog" aria-modal="true">
			<div class="so-head">
				<div>
					<div class="t">Assign to {{ company.company_name }}</div>
					<div class="s">
						Map an existing customer to this company and set their role
					</div>
				</div>
				<button class="iconbtn" @click="$emit('close')">
					<FeatherIcon name="x" />
				</button>
			</div>

			<div class="so-body">
				<div>
					<label class="flabel">Customer</label>
					<select v-model="form.user" class="finput">
						<option value="" disabled>Select customer…</option>
						<option v-for="c in customers.data ?? []" :key="c.name" :value="c.name">
							{{ c.customer_name || c.name }}
						</option>
					</select>
				</div>

				<div>
					<label class="flabel">Role in company</label>
					<div class="chiprow">
						<button
							type="button"
							:class="['chip', form.designation === 'Manager' ? 'on' : '']"
							@click="form.designation = 'Manager'"
						>
							Manager
						</button>
						<button
							type="button"
							:class="['chip', form.designation === 'User' ? 'on' : '']"
							@click="form.designation = 'User'"
						>
							User
						</button>
					</div>
					<div class="fhint">
						Managers can see every request raised by anyone in this company.
					</div>
				</div>
			</div>

			<div class="so-foot">
				<span class="grow"></span>
				<button class="btn" @click="$emit('close')">Cancel</button>
				<button class="btn primary" :disabled="!form.user || submitting" @click="submit">
					{{ submitting ? 'Assigning…' : 'Assign' }}
				</button>
			</div>
		</div>
	</teleport>
</template>

<script setup>
import { ref } from 'vue'
import { createResource, FeatherIcon } from 'frappe-ui'

const props = defineProps({
	company: { type: Object, required: true },
})
const emit = defineEmits(['close', 'assigned'])

const form = ref({ user: '', designation: 'User' })
const submitting = ref(false)

// Load customers via the same whitelisted API the request-create dialog uses
const customers = createResource({
	url: 'onboardpro.api.search_customers',
	params: { query: '', limit: 500 },
	auto: true,
})

const assign = createResource({
	url: 'onboardpro.api.assign_customer',
	onSuccess() {
		submitting.value = false
		emit('assigned')
	},
	onError() {
		submitting.value = false
	},
})

function submit() {
	if (!form.value.user) return
	submitting.value = true
	assign.submit({
		user: form.value.user,
		company: props.company.name,
		designation: form.value.designation,
	})
}
</script>
