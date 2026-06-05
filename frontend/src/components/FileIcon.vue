<template>
	<span :class="['fileicon', cls]">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ ext: { type: String, default: 'doc' } })

const KNOWN = ['xlsx', 'csv', 'pdf', 'zip', 'doc']
const cls = computed(() => {
	const e = (props.ext || 'doc').toLowerCase()
	return KNOWN.includes(e) ? e : 'doc'
})
const label = computed(() => cls.value.slice(0, 4).toUpperCase())
</script>
