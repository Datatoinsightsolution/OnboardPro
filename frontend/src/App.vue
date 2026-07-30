<template>
	<!-- Auth check in progress -->
	<div v-if="loading" class="auth-loading">
		<div class="auth-spinner"></div>
	</div>

	<!-- Authenticated app shell -->
	<div v-else class="app">
		<AppSidebar
			:open-count="openCount"
			:overdue-count="overdueCount"
			:role="role"
			:user-name="userName"
			:open="sidebarOpen"
		/>
		<div v-if="sidebarOpen" class="mob-sidebar-scrim" @click="sidebarOpen = false" />

		<div class="main">
			<!-- Topbar -->
			<div class="topbar">
				<button class="mob-menu-btn" @click="sidebarOpen = !sidebarOpen">
					<FeatherIcon name="menu" />
				</button>
				<div class="crumb">
					<span class="root" @click="router.push('/')">
						{{
							role === 'customer'
								? isManager
									? 'Team requests'
									: 'My requests'
								: 'Requests'
						}}
					</span>
					<template v-if="route.name === 'RequestDetail'">
						<FeatherIcon
							name="chevron-right"
							style="width: 15px; height: 15px; color: var(--ink-4); flex: none"
						/>
						<span class="here">{{ pageTitle || route.params.id }}</span>
					</template>
					<template v-else-if="route.name === 'Dashboard'">
						<FeatherIcon
							name="chevron-right"
							style="width: 15px; height: 15px; color: var(--ink-4); flex: none"
						/>
						<span class="here">Dashboard</span>
					</template>
					<template v-else-if="route.name === 'Companies'">
						<FeatherIcon
							name="chevron-right"
							style="width: 15px; height: 15px; color: var(--ink-4); flex: none"
						/>
						<span class="here">Companies</span>
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
					:is-manager="isManager"
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
import { ref, watch, provide, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeRequest, FeatherIcon } from 'frappe-ui'
import { dateKey } from '@/utils/helpers'
import AppSidebar from '@/components/AppSidebar.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const role = ref('staff')
const isManager = ref(false)
const userName = ref('')
const pageTitle = ref('')
const openCount = ref(0)
const overdueCount = ref(0)
// Seeded from the server on mount so date buckets follow system time, not the browser's.
const serverToday = ref(dateKey())
const toasts = ref([])
const sidebarOpen = ref(false)

watch(route, () => {
	sidebarOpen.value = false
})

onMounted(async () => {
	try {
		const r = await frappeRequest({ url: 'onboardpro.api.get_session_role' })
		role.value = r.role
		userName.value = r.full_name
		isManager.value = !!r.is_manager
		serverToday.value = r.today || dateKey()
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

function onRequestsLoaded({ open, overdue }) {
	openCount.value = open
	overdueCount.value = overdue ?? 0
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
provide('serverToday', serverToday)
</script>
