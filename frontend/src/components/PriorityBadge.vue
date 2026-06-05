<template>
	<span class="prio" :data-tone="tone">
		<span class="bars" aria-hidden="true">
			<i
				v-for="i in 4"
				:key="i"
				:class="i <= level ? 'on' : ''"
				:style="{ height: 5 + (i - 1) * 2.3 + 'px' }"
			/>
		</span>
		{{ priority }}
	</span>
</template>

<script setup>
import { computed } from 'vue'
import { PRIORITY_META } from '@/utils/helpers'

const props = defineProps({ priority: { type: String, default: 'Medium' } })
const meta = computed(() => PRIORITY_META[props.priority] ?? PRIORITY_META.Medium)
const tone = computed(() => meta.value.tone)
const level = computed(() => 4 - meta.value.rank)
</script>
