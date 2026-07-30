<template>
	<teleport to="body">
		<!-- .stack sits above a slideover's scrim so this can be opened from inside one -->
		<div class="scrim stack" @click="$emit('close')"></div>
		<div class="modal" role="dialog" aria-modal="true">
			<div class="modal-head">
				<div class="modal-ic" :data-tone="tone">
					<FeatherIcon :name="icon" />
				</div>
				<div class="t">{{ title }}</div>
			</div>
			<div class="modal-body"><slot /></div>
			<div class="modal-foot">
				<button class="btn" @click="$emit('close')">Cancel</button>
				<button class="btn primary" :disabled="busy" @click="$emit('confirm')">
					{{ busy ? 'Saving…' : confirmLabel }}
				</button>
			</div>
		</div>
	</teleport>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
	title: { type: String, required: true },
	tone: { type: String, default: 'amber' },
	icon: { type: String, default: 'alert-triangle' },
	confirmLabel: { type: String, default: 'Confirm' },
	busy: { type: Boolean, default: false },
})
defineEmits(['confirm', 'close'])
</script>
