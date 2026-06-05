<template>
	<span class="slachip" :data-tone="cssTone"> <span class="heart"></span>{{ s.label }} </span>
</template>

<script setup>
import { computed } from 'vue'
import { sla, toMs, SLA_TONE_MAP, PRIORITY_META } from '@/utils/helpers'

const props = defineProps({
	deadline: { type: [Number, String], default: null }, // ms timestamp OR ISO string
	now: { type: Number, required: true },
	windowH: { type: Number, default: 48 },
	state: { type: String, default: null }, // fr_state / res_state if already known
})

const s = computed(() => {
	if (props.state === 'Fulfilled') return { tone: 'ok', label: 'Fulfilled' }
	if (props.state === 'Failed') return { tone: 'breach', label: 'Failed' }
	if (props.state === 'Paused') return { tone: 'ok', label: 'Paused' }
	const ms = typeof props.deadline === 'string' ? toMs(props.deadline) : props.deadline ?? 0
	return sla(ms, props.now, props.windowH)
})

const cssTone = computed(() => SLA_TONE_MAP[s.value.tone] ?? 'slate')
</script>
