import { createRouter, createWebHistory } from 'vue-router'
import Requests from '@/pages/Requests.vue'
import RequestDetail from '@/pages/RequestDetail.vue'
import Dashboard from '@/pages/Dashboard.vue'
import Companies from '@/pages/Companies.vue'

export default createRouter({
	history: createWebHistory('/onboardpro/'), // ← update to your app path
	routes: [
		{ path: '/', name: 'Requests', component: Requests },
		{ path: '/dashboard', name: 'Dashboard', component: Dashboard },
		{ path: '/request/:id', name: 'RequestDetail', component: RequestDetail, props: true },
		{ path: '/companies', name: 'Companies', component: Companies },
	],
})
