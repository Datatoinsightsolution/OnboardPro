<template>
	<span class="pill" :data-tone="meta.tone" style="gap: 6px">
		<FeatherIcon :name="meta.icon" style="width: 12px; height: 12px" />
		{{ meta.label }}<template v-if="days"> · {{ days }}d</template>
	</span>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { deliveryState, dayDiff, DELIVERY_META } from '@/utils/helpers'

const props = defineProps({
	request: { type: Object, required: true },
	today: { type: String, required: true }, // 'YYYY-MM-DD', server-authoritative
})

const state = computed(() => deliveryState(props.request, props.today))
const meta = computed(() => DELIVERY_META[state.value] ?? DELIVERY_META.awaiting)

// How far past the date that mattered. For nocommit that's the expected date, since
// there is no commitment to measure against.
const days = computed(() => {
	const r = props.request
	if (state.value === 'overdue') return dayDiff(props.today, r.delivery_date)
	if (state.value === 'nocommit') return dayDiff(props.today, r.expected_date)
	if (state.value === 'late') return dayDiff(r.resolved_on, r.delivery_date)
	return 0
})
</script>
