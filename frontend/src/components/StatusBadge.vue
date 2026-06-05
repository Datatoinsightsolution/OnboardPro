<template>
	<span :class="['statuspill', isClosed ? 'closed' : '']" :data-tone="tone">
		<span class="ring"></span>{{ status }}
	</span>
</template>

<script setup>
import { computed } from 'vue'
import { STATUS_META } from '@/utils/helpers'

const props = defineProps({ status: { type: String, default: 'Open' } })
const tone = computed(() => STATUS_META[props.status]?.tone ?? 'slate')
const isClosed = computed(() => STATUS_META[props.status]?.group === 'closed')
</script>
