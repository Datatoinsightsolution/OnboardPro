<template>
	<teleport to="body">
		<div class="scrim" @click="$emit('close')"></div>
		<div class="slideover" role="dialog" aria-modal="true">
			<div class="so-head">
				<div>
					<div class="t">{{ isAmend ? 'Amend delivery date' : 'Commit delivery date' }}</div>
					<div class="s">{{ request.subject }}</div>
				</div>
				<button class="iconbtn" @click="$emit('close')">
					<FeatherIcon name="x" />
				</button>
			</div>

			<div class="so-body">
				<!-- Context: what was asked for -->
				<div class="field">
					<span class="k">Expected</span>
					<span class="v">{{ fmtDay(request.expected_date) }}</span>
				</div>
				<div v-if="isAmend" class="field">
					<span class="k">Committed</span>
					<span class="v">{{ fmtDay(request.delivery_date) }}</span>
				</div>

				<div>
					<label class="flabel">
						Delivery date
						<span data-tone="red" style="color: var(--t-ink)">*</span>
					</label>
					<input v-model="date" type="date" class="finput" :min="todayStr" />
					<div class="fhint">
						{{
							isAmend
								? 'Amending a committed date. The change will be recorded in the request timeline.'
								: 'You can only set this once. After you confirm, only the OnboardPro team can change it.'
						}}
					</div>
				</div>

				<!-- Slipping past what was asked for is allowed, but never silent -->
				<div v-if="slipDays > 0" class="warnbox" data-tone="amber">
					<FeatherIcon name="alert-triangle" />
					<div>
						That's <b>{{ slipDays }} day{{ slipDays === 1 ? '' : 's' }}</b> after the
						expected date of <b>{{ fmtDay(request.expected_date) }}</b
						>. You can still commit to it — we'll flag the gap to the team.
					</div>
				</div>
			</div>

			<div class="so-foot">
				<span class="grow"></span>
				<button class="btn" @click="$emit('close')">Cancel</button>
				<button class="btn primary" :disabled="!date || busy" @click="confirming = true">
					<FeatherIcon name="calendar" style="width: 14px; height: 14px" />
					{{ isAmend ? 'Amend date' : 'Commit date' }}
				</button>
			</div>
		</div>

		<ConfirmDialog
			v-if="confirming"
			:title="isAmend ? 'Amend the committed date?' : 'Commit to this delivery date?'"
			:tone="isAmend ? 'amber' : 'red'"
			:icon="isAmend ? 'edit-3' : 'lock'"
			:confirm-label="isAmend ? 'Yes, amend' : 'Yes, commit'"
			:busy="busy"
			@close="confirming = false"
			@confirm="$emit('committed', date)"
		>
			<template v-if="isAmend">
				Moving the delivery date from <b>{{ fmtDay(request.delivery_date) }}</b> to
				<b>{{ fmtDay(date) }}</b
				>. This will be recorded in the request timeline.
			</template>
			<template v-else>
				You are committing to deliver by <b>{{ fmtDay(date) }}</b
				>. This cannot be changed once confirmed.
				<template v-if="slipDays > 0">
					It is {{ slipDays }} day{{ slipDays === 1 ? '' : 's' }} after the expected date.
				</template>
			</template>
		</ConfirmDialog>
	</teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { fmtDay, dateKey, dayDiff } from '@/utils/helpers'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const props = defineProps({
	request: { type: Object, required: true },
	busy: { type: Boolean, default: false },
})
defineEmits(['close', 'committed'])

const isAmend = computed(() => !!props.request.delivery_date)
const todayStr = dateKey()
const date = ref(props.request.delivery_date ? String(props.request.delivery_date).slice(0, 10) : '')
const confirming = ref(false)

const slipDays = computed(() => {
	if (!date.value || !props.request.expected_date) return 0
	return dayDiff(date.value, props.request.expected_date)
})
</script>
