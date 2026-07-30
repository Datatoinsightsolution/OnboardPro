<template>
	<div class="detail" v-if="doc.doc">
		<!-- Main: timeline + composer -->
		<div class="detail-main">
			<div class="detail-head">
				<div class="subj">{{ doc.doc.subject }}</div>
				<div class="sub">
					<span class="id">#{{ doc.doc.name }}</span>
					<span class="dot-sep"></span>
					<StatusBadge :status="doc.doc.status" />
					<span class="dot-sep"></span>
					<DeliveryChip :request="doc.doc" :today="today" />
					<span class="dot-sep"></span>
					<span>Opened {{ fmtAgo(toMs(doc.doc.creation), now) }}</span>
					<span class="dot-sep"></span>
					<span>{{ doc.doc.customer_name || doc.doc.customer }}</span>
				</div>
			</div>

			<div ref="scrollEl" class="detail-scroll">
				<!-- Description -->
				<div class="descblock">
					<p>{{ doc.doc.description || 'No description provided.' }}</p>
					<div class="dl">
						<span class="pill" data-tone="slate" style="gap: 6px">
							<FeatherIcon
								:name="DATATYPE_ICON[doc.doc.data_type] || 'file'"
								style="width: 12px; height: 12px"
							/>
							{{ doc.doc.data_type }}
						</span>
						<PriorityBadge :priority="doc.doc.priority" />
					</div>
				</div>

				<!-- Attachments -->
				<div class="section-label">Data &amp; attachments</div>
				<div class="attach-grid">
					<div
						v-if="!attachments.length"
						style="font-size: 13px; color: var(--ink-4); margin-bottom: 4px"
					>
						No files yet.
					</div>
					<div v-for="a in attachments" :key="a.name" class="attach-row">
						<a class="attach" :href="a.file_url" target="_blank">
							<FileIcon :ext="fileExt(a.file_name)" />
							<div class="fmeta">
								<div class="fn">{{ a.file_name }}</div>
								<div class="fs">
									{{
										a.file_size ? (a.file_size / 1024).toFixed(0) + ' KB' : ''
									}}
									· {{ a.attached_to_name }}
								</div>
							</div>
						</a>
						<span class="by">{{ fmtAgo(toMs(a.creation), now) }}</span>
					</div>
					<div
						v-if="doc.doc.status !== 'Resolved'"
						class="dropzone"
						@click="triggerUpload"
					>
						<FeatherIcon name="upload" />
						<div class="big">
							{{ role === 'customer' ? 'Upload your data here' : 'Attach a file' }}
						</div>
						<div class="sm">
							{{
								role === 'customer'
									? 'Drag a file or click to browse — XLSX, CSV, PDF, ZIP'
									: 'Drag & drop or click to browse'
							}}
						</div>
					</div>
					<input
						ref="fileInput"
						type="file"
						style="display: none"
						@change="handleUpload"
					/>
				</div>

				<!-- Activity -->
				<div class="section-label" style="margin-top: 28px">Activity</div>
				<div class="timeline">
					<template v-for="(ev, i) in timeline" :key="i">
						<!-- Message bubble -->
						<div v-if="ev.kind === 'msg'" :class="['msg', ev.isSelf ? 'self' : '']">
							<div class="msg-av">
								<RistoAvatar
									:name="ev.owner_name || ev.owner"
									:role="ev.isStaff ? 'staff' : 'customer'"
									:size="28"
								/>
							</div>
							<div class="bubble">
								<div class="bhead">
									<span class="nm">{{ ev.owner_name || ev.owner }}</span>
									<span :class="['tag', ev.isStaff ? 'staff' : 'customer']">{{
										ev.isStaff ? 'User' : 'Customer'
									}}</span>
									<span class="when">{{ fmtAgo(toMs(ev.creation), now) }}</span>
								</div>
								<div class="btext">{{ ev.content }}</div>
							</div>
						</div>

						<!-- System event -->
						<div v-else class="tl-item">
							<div class="tl-node" :data-tone="ev.tone || undefined">
								<FeatherIcon :name="ev.icon" style="width: 13px; height: 13px" />
							</div>
							<div class="tl-event">
								<span v-html="ev.html"></span>
								<span class="when">{{ fmtAgo(toMs(ev.creation), now) }}</span>
							</div>
						</div>
					</template>

					<!-- Typing indicator -->
					<div v-if="false" class="typing">
						<span>Typing</span>
						<span class="dots"><i></i><i></i><i></i></span>
					</div>
				</div>
			</div>

			<!-- Composer -->
			<div class="composer">
				<!-- Collapsed: Reply button -->
				<div v-if="!replyOpen" class="reply-trigger">
					<button class="btn reply-btn" @click="openReply">
						<FeatherIcon name="corner-up-left" style="width: 15px; height: 15px" />
						Reply
					</button>
				</div>

				<!-- Expanded: full composer -->
				<div v-else class="composer-box">
					<textarea
						ref="taRef"
						v-model="message"
						:placeholder="
							role === 'customer'
								? 'Reply to Risto…'
								: 'Reply to ' + (doc.doc.customer_name || 'customer') + '…'
						"
						@input="growTa"
						@keydown.ctrl.enter.prevent="sendMessage"
						@keydown.meta.enter.prevent="sendMessage"
						@keydown.esc="replyOpen = false"
					/>
					<div class="composer-bar">
						<button class="iconbtn" title="Attach file" @click="triggerUpload">
							<FeatherIcon name="paperclip" />
						</button>
						<span class="grow"></span>
						<span class="as"
							>Posting as
							<b style="color: var(--ink-2)">{{ currentUserName }}</b></span
						>
						<button class="btn sm" @click="replyOpen = false">Cancel</button>
						<button
							class="btn primary sm"
							:disabled="!message.trim() || sending"
							@click="sendMessage"
						>
							<FeatherIcon name="send" style="width: 14px; height: 14px" />Send
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Right rail -->
		<aside class="rail">
			<!-- Status -->
			<div class="rail-card">
				<h3>Status</h3>
				<!-- Staff: interactive dropdown -->
				<div v-if="role === 'staff'" class="statussel" ref="statusRef">
					<button @click="statusOpen = !statusOpen">
						<StatusBadge :status="doc.doc.status" />
						<FeatherIcon
							name="chevron-down"
							class="chev"
							style="width: 16px; height: 16px"
						/>
					</button>
					<div v-if="statusOpen" class="menu">
						<button v-for="s in STATUSES" :key="s" @click="updateStatus(s)">
							<StatusBadge :status="s" />
							<FeatherIcon
								v-if="s === doc.doc.status"
								name="check"
								class="check"
								style="width: 15px; height: 15px"
							/>
						</button>
					</div>
				</div>
				<!-- Customer: read-only badge -->
				<div v-else style="padding: 4px 0">
					<StatusBadge :status="doc.doc.status" />
				</div>
			</div>

			<!-- Delivery -->
			<div class="rail-card">
				<h3>Delivery</h3>

				<div class="field">
					<span class="k">Expected</span>
					<span class="v">{{ fmtDay(doc.doc.expected_date) }}</span>
				</div>

				<template v-if="doc.doc.delivery_date">
					<div class="field">
						<span class="k">Delivery</span>
						<span class="v">{{ fmtDay(doc.doc.delivery_date) }}</span>
					</div>
					<div class="field">
						<span class="k">Status</span>
						<span class="v"><DeliveryChip :request="doc.doc" :today="today" /></span>
					</div>
					<!-- Settled state reads as settled: a lock, not a disabled input -->
					<div class="lockrow">
						<FeatherIcon name="lock" />
						<span v-if="doc.doc.delivery_committed_on">
							Committed {{ fmtAgo(toMs(doc.doc.delivery_committed_on), now) }} —
							locked
						</span>
						<span v-else>Locked</span>
					</div>
					<button
						v-if="role === 'staff'"
						class="btn sm"
						style="margin-top: 10px"
						@click="deliveryOpen = true"
					>
						<FeatherIcon name="edit-3" style="width: 13px; height: 13px" />Amend
					</button>
				</template>

				<template v-else>
					<div class="field">
						<span class="k">Delivery</span>
						<span class="v"><DeliveryChip :request="doc.doc" :today="today" /></span>
					</div>
					<!-- Gate on the actual write permission, not the role: has_permission grants
					     company Managers read-only, so a role check would show them a 403 button. -->
					<template v-if="canCommit">
						<button
							class="btn primary sm"
							style="margin-top: 10px"
							@click="deliveryOpen = true"
						>
							<FeatherIcon name="calendar" style="width: 13px; height: 13px" />
							Commit delivery date
						</button>
						<div class="fhint">You can only set this once.</div>
					</template>
					<button
						v-else-if="role === 'staff'"
						class="btn sm"
						style="margin-top: 10px"
						@click="deliveryOpen = true"
					>
						<FeatherIcon name="calendar" style="width: 13px; height: 13px" />
						Set on behalf
					</button>
				</template>

				<div v-if="doc.doc.resolved_on" class="field" style="margin-top: 10px">
					<span class="k">Resolved</span>
					<span class="v">{{ fmtDay(doc.doc.resolved_on) }}</span>
				</div>
			</div>

			<!-- Details -->
			<div class="rail-card">
				<h3>Details</h3>
				<div class="field">
					<span class="k">Priority</span>
					<span class="v"><PriorityBadge :priority="doc.doc.priority" /></span>
				</div>
				<div class="field">
					<span class="k">Data type</span>
					<span class="v">
						<FeatherIcon
							:name="DATATYPE_ICON[doc.doc.data_type] || 'file'"
							style="width: 15px; height: 15px; color: var(--ink-3)"
						/>
						{{ doc.doc.data_type }}
					</span>
				</div>
				<div class="field">
					<span class="k">Owner</span>
					<span class="v">
						<RistoAvatar
							:name="doc.doc.assignee_name || doc.doc.assignee || '?'"
							role="staff"
							:size="20"
						/>
						{{ doc.doc.assignee_name || doc.doc.assignee }}
					</span>
				</div>
				<div class="field">
					<span class="k">Customer</span>
					<span class="v">
						<RistoAvatar
							:name="doc.doc.customer_name || doc.doc.customer"
							role="customer"
							:size="20"
						/>
						{{ doc.doc.customer_name || doc.doc.customer }}
					</span>
				</div>
				<div class="field">
					<span class="k">Created</span>
					<span class="v">{{ fmtDate(toMs(doc.doc.creation)) }}</span>
				</div>
			</div>
		</aside>

		<DeliveryDateDialog
			v-if="deliveryOpen"
			:request="doc.doc"
			:busy="committing"
			@close="deliveryOpen = false"
			@committed="commitDelivery"
		/>
	</div>

	<!-- Loading -->
	<div
		v-else
		style="display: flex; align-items: center; justify-content: center; flex: 1; height: 100%"
	>
		<div
			style="
				width: 24px;
				height: 24px;
				border: 2px solid var(--accent);
				border-top-color: transparent;
				border-radius: 99px;
				animation: spin 0.7s linear infinite;
			"
		></div>
	</div>
</template>

<script setup>
import { ref, computed, watch, nextTick, inject, onMounted, onUnmounted } from 'vue'
import { createDocumentResource, FeatherIcon, frappeRequest } from 'frappe-ui'
import { fmtAgo, fmtDate, fmtDay, toMs, dateKey, DATATYPE_ICON } from '@/utils/helpers'
import StatusBadge from '@/components/StatusBadge.vue'
import PriorityBadge from '@/components/PriorityBadge.vue'
import DeliveryChip from '@/components/DeliveryChip.vue'
import DeliveryDateDialog from '@/components/DeliveryDateDialog.vue'
import RistoAvatar from '@/components/RistoAvatar.vue'
import FileIcon from '@/components/FileIcon.vue'

const props = defineProps({
	id: { type: String, required: true },
	role: { type: String, default: 'staff' },
})
const emit = defineEmits(['set-title'])
const toast = inject('toast', () => {})
// Server-authoritative date, so buckets don't drift with the browser's timezone.
const serverToday = inject('serverToday', ref(dateKey()))
const today = computed(() => serverToday.value)

const now = ref(Date.now())
const message = ref('')
const sending = ref(false)
const replyOpen = ref(false)
const statusOpen = ref(false)
const deliveryOpen = ref(false)
const committing = ref(false)
const scrollEl = ref(null)
const taRef = ref(null)
const fileInput = ref(null)
const statusRef = ref(null)

const STATUSES = ['Open', 'In Review', 'Needs Revision', 'Resolved']

const timer = setInterval(() => {
	now.value = Date.now()
}, 1000)
onUnmounted(() => clearInterval(timer))

onMounted(() => {
	// Close status menu on outside click
	document.addEventListener('mousedown', (e) => {
		if (statusRef.value && !statusRef.value.contains(e.target)) statusOpen.value = false
	})
	// Mark this request as seen so the unread indicator clears
	if (props.role === 'staff') {
		frappeRequest({ url: 'onboardpro.api.mark_seen', params: { docname: props.id } })
	}
})

// Document
const doc = createDocumentResource({
	doctype: 'Implementation Request',
	name: props.id,
	auto: true,
})

watch(
	() => doc.doc?.subject,
	(s) => {
		if (s) emit('set-title', s)
	}
)

// Activity: comments + status changes, merged and sorted by time
const activityData = ref([])
async function loadActivity() {
	activityData.value = await frappeRequest({
		url: 'onboardpro.api.get_activity',
		params: { docname: props.id },
	})
}
loadActivity()

// Attachments
const attachments = ref([])
async function loadAttachments() {
	attachments.value = await frappeRequest({
		url: 'onboardpro.api.get_attachments',
		params: { docname: props.id },
	})
}
loadAttachments()

// Build timeline from merged activity
const meEmail = window.frappe?.session?.user || ''
const currentUserName = window.frappe?.session?.user_fullname || meEmail
const timeline = computed(() =>
	activityData.value.map((ev) => ({
		...ev,
		isStaff: !!ev.is_staff,
		isSelf: ev.owner === meEmail,
	}))
)

// Scroll to bottom on new messages
watch(
	() => timeline.value.length,
	async () => {
		await nextTick()
		if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
	}
)

// Only the request's own customer may commit — has_permission gives company Managers
// read access but not write, so gating on `role` alone would offer them a 403 button.
const canCommit = computed(() => props.role === 'customer' && doc.doc?.customer_email === meEmail)

async function commitDelivery(date) {
	committing.value = true
	try {
		// delivery_committed_on is stamped server-side in validate() and comes back in
		// the set_value response, so the rail updates without a second fetch.
		await doc.setValue.submit({ delivery_date: date })
		deliveryOpen.value = false
		toast('Delivery date set')
		await loadActivity()
	} finally {
		committing.value = false
	}
}

async function openReply() {
	replyOpen.value = true
	await nextTick()
	taRef.value?.focus()
}

// Send message
async function sendMessage() {
	const text = message.value.trim()
	if (!text || sending.value) return
	sending.value = true
	try {
		await frappeRequest({
			url: 'onboardpro.api.add_comment',
			params: { docname: props.id, content: text },
		})
		message.value = ''
		replyOpen.value = false
		if (taRef.value) taRef.value.style.height = 'auto'
		await loadActivity()
	} finally {
		sending.value = false
	}
}

function growTa() {
	const t = taRef.value
	if (t) {
		t.style.height = 'auto'
		t.style.height = Math.min(160, t.scrollHeight) + 'px'
	}
}

// Update status
async function updateStatus(s) {
	statusOpen.value = false
	if (s === doc.doc.status) return
	await doc.setValue.submit({ status: s })
	toast('Status → ' + s)
	await loadActivity()
}

// File upload
function triggerUpload() {
	fileInput.value?.click()
}

async function handleUpload(e) {
	const file = e.target.files?.[0]
	if (!file) return
	const fd = new FormData()
	fd.append('file', file)
	fd.append('doctype', 'Implementation Request')
	fd.append('docname', props.id)
	await fetch('/api/method/upload_file', {
		method: 'POST',
		body: fd,
		headers: { 'X-Frappe-CSRF-Token': window.frappe?.csrf_token ?? '' },
	})
	await loadAttachments()
	toast('File attached')
}

function fileExt(name) {
	return (name || '').split('.').pop() || 'doc'
}
</script>
