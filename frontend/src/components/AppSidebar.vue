<template>
	<aside class="side">
		<!-- Brand -->
		<div class="brand">
			<div class="brand-mark">
				<FeatherIcon name="inbox" />
			</div>
			<div>
				<div class="brand-name">OnboardPro</div>
				<div class="brand-sub">Implementation Portal</div>
			</div>
		</div>

		<!-- Nav -->
		<nav class="nav">
			<div class="nav-label">Workspace</div>

			<router-link to="/pulse" custom v-slot="{ navigate, isActive }">
				<button :class="['nav-item', isActive ? 'active' : '']" @click="navigate">
					<FeatherIcon name="activity" />
					SLA Pulse
					<span
						v-if="breachCount > 0"
						class="nav-count"
						style="color: var(--t-solid)"
						data-tone="red"
					>
						{{ breachCount }}
					</span>
				</button>
			</router-link>

			<router-link to="/" custom v-slot="{ navigate, isActive }">
				<button
					:class="['nav-item', isActive && route.name !== 'Pulse' ? 'active' : '']"
					@click="navigate"
				>
					<FeatherIcon name="inbox" />
					Requests
					<span class="nav-count">{{ openCount }}</span>
				</button>
			</router-link>
		</nav>

		<!-- Footer -->
		<div class="side-foot">
			<!-- Popover menu -->
			<div v-if="menuOpen" class="user-menu">
				<a
					:href="helpdeskUrl"
					target="_blank"
					rel="noopener noreferrer"
					class="user-menu-item"
					@click="menuOpen = false"
				>
					<FeatherIcon name="headphones" />
					Helpdesk
				</a>
				<button class="user-menu-item danger" @click="logout">
					<FeatherIcon name="log-out" />
					Log out
				</button>
			</div>

			<!-- User card trigger -->
			<button class="user-card" @click="menuOpen = !menuOpen">
				<RistoAvatar :name="currentUser" :role="role" :size="32" />
				<div class="user-card-info">
					<div class="user-card-name">{{ currentUser }}</div>
					<div class="user-card-role">
						{{ role === 'staff' ? 'User' : 'Customer' }}
					</div>
				</div>
				<FeatherIcon
					class="user-card-caret"
					:name="menuOpen ? 'chevron-up' : 'chevron-down'"
					style="width: 14px; height: 14px"
				/>
			</button>
		</div>
	</aside>

	<!-- Click-outside scrim -->
	<div v-if="menuOpen" class="menu-scrim" @click="menuOpen = false" />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import RistoAvatar from '@/components/RistoAvatar.vue'

const props = defineProps({
	openCount: { type: Number, default: 0 },
	breachCount: { type: Number, default: 0 },
	role: { type: String, default: 'staff' },
	userName: { type: String, default: '' },
})

const route = useRoute()
const menuOpen = ref(false)
const helpdeskUrl = `${window.location.protocol}//${window.location.hostname}/helpdesk`
const currentUser = computed(
	() => props.userName || window.frappe?.session?.user_fullname || 'User'
)

async function logout() {
	try {
		await fetch('/api/method/logout', {
			method: 'POST',
			headers: { 'X-Frappe-CSRF-Token': window.frappe?.csrf_token || 'fetch' },
		})
	} finally {
		window.location.href = '/login'
	}
}
</script>
