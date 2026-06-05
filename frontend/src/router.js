import { createRouter, createWebHistory } from 'vue-router'
import Requests from '@/pages/Requests.vue'
import RequestDetail from '@/pages/RequestDetail.vue'
import Pulse from '@/pages/Pulse.vue'

export default createRouter({
	history: createWebHistory('/onboardpro/'), // ← update to your app path
	routes: [
		{ path: '/', name: 'Requests', component: Requests },
		{ path: '/pulse', name: 'Pulse', component: Pulse },
		{ path: '/request/:id', name: 'RequestDetail', component: RequestDetail, props: true },
	],
})
