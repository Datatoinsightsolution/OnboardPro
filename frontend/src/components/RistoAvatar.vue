<template>
	<div :class="['av', roleClass, 'av-sz-' + size]" :title="name">{{ initials(name) }}</div>
</template>

<script setup>
import { computed } from 'vue'
import { initials } from '@/utils/helpers'

const props = defineProps({
	name: { type: String, default: '?' },
	role: { type: String, default: 'staff' }, // 'staff' | 'customer'
	size: { type: Number, default: 32 },
})

const roleClass = computed(() => (props.role === 'staff' ? 'staff' : 'customer'))
</script>
