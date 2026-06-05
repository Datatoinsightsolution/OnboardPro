<template>
	<!-- Auth check in progress -->
	<div v-if="loading" class="auth-loading">
		<div class="auth-spinner"></div>
	</div>

	<!-- Authenticated app shell -->
	<div v-else class="app">
		<AppSidebar :open-count="openCount" :breach-count="breachCount" :role="role" />

		<div class="main">
			<!-- Topbar -->
			<div class="topbar">
				<div class="crumb">
					<span class="root" @click="router.push('/')">
						{{ role === 'customer' ? 'My requests' : 'Requests' }}
					</span>
					<template v-if="route.name === 'RequestDetail'">
						<FeatherIcon
							name="chevron-right"
							style="width: 15px; height: 15px; color: var(--ink-4); flex: none"
						/>
						<span class="here">{{ pageTitle || route.params.id }}</span>
					</template>
					<template v-else-if="route.name === 'Pulse'">
						<FeatherIcon
							name="chevron-right"
							style="width: 15px; height: 15px; color: var(--ink-4); flex: none"
						/>
						<span class="here">SLA Pulse</span>
					</template>
				</div>
				<span class="grow"></span>
				<button
					v-if="route.name === 'RequestDetail'"
					class="btn"
					@click="router.push('/')"
				>
					<FeatherIcon name="x" style="width: 14px; height: 14px" />Close
				</button>
			</div>

			<!-- Page content -->
			<div class="viewport">
				<router-view
					:role="role"
					@requests-loaded="onRequestsLoaded"
					@set-title="pageTitle = $event"
				/>
			</div>
		</div>

		<!-- Toasts -->
		<div class="toasts">
			<div v-for="t in toasts" :key="t.id" class="toast">
				<FeatherIcon name="check-circle" class="tk" style="width: 16px; height: 16px" />
				{{ t.msg }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeRequest, FeatherIcon } from 'frappe-ui'
import AppSidebar from '@/components/AppSidebar.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const role = ref('staff')
const pageTitle = ref('')
const openCount = ref(0)
const breachCount = ref(0)
const toasts = ref([])

onMounted(async () => {
	try {
		const r = await frappeRequest({ url: 'onboardpro.api.get_session_role' })
		role.value = r
		loading.value = false
	} catch {
		// Not logged in or session expired — hand off to Frappe's login page
		redirectToLogin()
	}
})

function redirectToLogin() {
	const next = encodeURIComponent(window.location.pathname || '/onboardpro')
	window.location.href = `/login?redirect-to=${next}`
}

function onRequestsLoaded({ open, breach }) {
	openCount.value = open
	breachCount.value = breach
}

function toast(msg) {
	const id = Math.random()
	toasts.value.push({ id, msg })
	setTimeout(() => {
		toasts.value = toasts.value.filter((t) => t.id !== id)
	}, 2600)
}

provide('toast', toast)
provide('role', role)
</script>
