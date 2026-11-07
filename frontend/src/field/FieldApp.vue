<template>
  <div
    class="field-app"
    :class="{
      'field-dark': darkMode,
      'in-inspection': screen === 'inspection',
    }"
  >
    <header class="field-header">
      <button
        class="field-brand brand-button"
        aria-label="ServiceMS Field home"
        :disabled="navigationLocked"
        @click="navigate('jobs')"
      >
        <span class="field-logo">S</span
        ><span>ServiceMS <strong>Field</strong></span>
      </button>
      <div class="field-header-actions">
        <span class="connection" :class="{ offline: !online }"
          ><i></i>{{ online ? 'Online' : 'Offline' }}</span
        ><button
          class="icon-button"
          :aria-label="darkMode ? 'Light theme' : 'Dark theme'"
          @click="darkMode = !darkMode"
        >
          <FieldIcon :name="darkMode ? 'sun' : 'moon'" /></button
        ><button
          class="avatar-button"
          aria-label="Account"
          :disabled="navigationLocked"
          @click="navigate('account')"
        >
          {{ fieldUser.slice(0, 1).toUpperCase() }}
        </button>
      </div>
    </header>
    <main class="field-main">
      <div v-if="error" class="alert error" role="alert">
        <FieldIcon name="alert-circle" /><span>{{ error }}</span
        ><button
          class="icon-button"
          aria-label="Dismiss error"
          @click="error = ''"
        >
          <FieldIcon name="x" />
        </button>
      </div>

      <section
        v-if="screen === 'jobs'"
        class="home-page"
        aria-label="Accessible job cards"
      >
        <div class="headline dashboard-heading">
          <div>
            <p class="eyebrow">YOUR WORKSHOP, IN VIEW</p>
            <h1>Welcome back<span class="greeting-dot">.</span></h1>
            <p class="muted">Your Job Cards, inspections and next steps.</p>
          </div>
          <button
            class="icon-button subtle"
            aria-label="Refresh Job Cards"
            :disabled="loading || historyLoading"
            @click="loadJobs"
          >
            <FieldIcon name="refresh-cw" />
          </button>
        </div>
        <div class="dashboard-stats">
          <button class="stat-card" @click="jobFilter = 'All'">
            <span class="stat-icon"><FieldIcon name="briefcase" /></span
            ><strong>{{ jobs.length }}</strong
            ><span>Job Cards</span></button
          ><button class="stat-card" @click="jobFilter = 'Draft'">
            <span class="stat-icon amber"><FieldIcon name="edit-3" /></span
            ><strong>{{
              historyLoading
                ? '—'
                : allInspections.filter((i) => i.inspection_status === 'Draft')
                    .length
            }}</strong
            ><span>Draft inspections</span></button
          ><button class="stat-card" @click="showCompletedHistory">
            <span class="stat-icon green"
              ><FieldIcon name="check-circle" /></span
            ><strong>{{
              historyLoading
                ? '—'
                : allInspections.filter(
                    (i) => i.inspection_status === 'Completed'
                  ).length
            }}</strong
            ><span>Completed</span>
          </button>
        </div>
        <div v-if="nextDraft" class="attention-card">
          <div>
            <span class="eyebrow">CONTINUE WHERE YOU LEFT OFF</span>
            <h2>{{ nextDraft.job.service_item_name }}</h2>
            <p>
              {{ stageLabel(nextDraft.inspection_stage) }} ·
              {{ nextDraft.name }}
            </p>
          </div>
          <button class="button primary" @click="openHistory(nextDraft)">
            Resume<FieldIcon name="arrow-right" />
          </button>
        </div>
        <div class="section-heading jobs-title">
          <div>
            <p class="eyebrow">READY WHEN YOU ARE</p>
            <h2>
              Your Job Cards
              <span class="muted">({{ filteredJobs.length }})</span>
            </h2>
          </div>
        </div>
        <div class="list-tools">
          <label class="search-input"
            ><FieldIcon name="search" /><input
              v-model="jobSearch"
              type="search"
              placeholder="Search registration, Job Card or workshop"
              aria-label="Search Job Cards"
          /></label>
          <label class="mobile-job-filter"
            >Filter
            <select v-model="jobFilter" aria-label="Filter Job Cards">
              <option value="All">All</option>
              <option value="Draft">Draft</option>
              <option value="Completed">Completed</option>
            </select>
          </label>
          <div
            class="filter-tabs desktop-job-filter"
            aria-label="Filter Job Cards"
          >
            <button
              v-for="filter in ['All', 'Draft', 'Completed']"
              :key="filter"
              :class="{ active: jobFilter === filter }"
              @click="jobFilter = filter"
            >
              {{
                filter === 'Draft'
                  ? 'With drafts'
                  : filter === 'Completed'
                  ? 'With completed'
                  : 'All'
              }}
            </button>
          </div>
        </div>
        <p v-if="historyLoading" class="muted loading-note" role="status">
          Loading inspection progress…
        </p>
        <div v-if="historyErrors.length" class="notice danger">
          Some inspection histories could not be loaded. Open a Job Card or
          refresh to retry.
        </div>
        <div v-if="loading" class="empty" role="status">
          Loading accessible Job Cards…
        </div>
        <div v-else-if="!filteredJobs.length" class="empty">
          <FieldIcon name="briefcase" />
          <h3>No Job Cards to show</h3>
          <p>
            {{
              jobs.length
                ? 'Try another search or filter.'
                : 'Your assigned work will appear here. Ask your manager to verify access.'
            }}
          </p>
        </div>
        <div v-else class="job-grid">
          <button
            v-for="job in filteredJobs"
            :key="job.name"
            class="job-card"
            @click="openJob(job)"
          >
            <span class="job-head"
              ><span class="vehicle-icon"><FieldIcon name="truck" /></span
              ><span class="status-tag">{{ job.status }}</span></span
            ><strong class="registration">{{ job.service_item_name }}</strong
            ><span class="vehicle-title">{{
              job.vehicle_model || 'Vehicle'
            }}</span
            ><span class="job-reference"
              >{{ job.name }} <span>·</span> {{ job.workshop }}</span
            ><span class="stage-indicators"
              ><span
                v-for="stage in stages"
                :key="stage"
                :class="stageClass(job.name, stage)"
                ><i></i>{{ stage === 'Pre-Service' ? 'Pre' : 'Post' }}
                <small>{{ stageStatus(job.name, stage) }}</small></span
              ></span
            ><span class="job-footer"
              >Open Job Card<FieldIcon name="arrow-right"
            /></span>
          </button>
        </div>
        <p v-if="jobs.length === 100" class="muted compact-note">
          Showing the latest 100 accessible Job Cards.
        </p>
      </section>

      <section
        v-else-if="screen === 'job' && selectedJob"
        class="job-page"
        aria-label="Selected Job Card"
      >
        <button class="back" @click="navigate('jobs')">
          <FieldIcon name="arrow-left" />All Job Cards
        </button>
        <div class="vehicle-hero">
          <span class="vehicle-icon"><FieldIcon name="truck" /></span
          ><span class="status-tag">{{ selectedJob.status }}</span>
          <p class="eyebrow">JOB CARD · {{ selectedJob.name }}</p>
          <h1>{{ selectedJob.service_item_name }}</h1>
          <p>{{ selectedJob.vehicle_model || 'Vehicle' }}</p>
        </div>
        <dl class="panel job-details detail-grid">
          <div>
            <dt><FieldIcon name="user" />Customer</dt>
            <dd>{{ selectedJob.customer || 'Not provided' }}</dd>
          </div>
          <div>
            <dt><FieldIcon name="map-pin" />Workshop</dt>
            <dd>{{ selectedJob.workshop }}</dd>
          </div>
        </dl>
        <div class="section-heading">
          <div>
            <p class="eyebrow">VEHICLE HANDOVER</p>
            <h2>Inspections</h2>
          </div>
          <span class="muted">Pre & Post</span>
        </div>
        <div class="stage-grid">
          <article
            v-for="stage in stages"
            :key="stage"
            class="panel stage-card"
          >
            <div class="section-heading">
              <span class="stat-icon"
                ><FieldIcon
                  :name="
                    stage === 'Pre-Service' ? 'log-in' : 'log-out'
                  " /></span
              ><span
                v-if="stageRecord(jobInspections, stage)"
                class="status-tag"
                :class="{
                  complete:
                    stageRecord(jobInspections, stage).inspection_status ===
                    'Completed',
                }"
                >{{
                  stageRecord(jobInspections, stage).inspection_status
                }}</span
              ><span v-else class="muted">Not started</span>
            </div>
            <h2>{{ stageLabel(stage) }}</h2>
            <p class="muted">
              {{
                stage === 'Pre-Service'
                  ? 'Record the vehicle condition before work begins.'
                  : 'Confirm the vehicle condition after service.'
              }}
            </p>
            <button
              v-if="stageRecord(jobInspections, stage)"
              class="button primary"
              :disabled="busy"
              @click="openInspection(stageRecord(jobInspections, stage).name)"
            >
              {{
                stageRecord(jobInspections, stage).inspection_status === 'Draft'
                  ? 'Resume Draft'
                  : 'View Inspection'
              }}<FieldIcon name="arrow-right" /></button
            ><button
              class="button"
              :class="
                stageRecord(jobInspections, stage) ? 'secondary' : 'primary'
              "
              :disabled="!online || busy"
              @click="chooseTemplate(stage)"
            >
              Start {{ stage === 'Pre-Service' ? 'Pre' : 'Post'
              }}<FieldIcon name="plus" />
            </button>
          </article>
        </div>
        <div class="panel history-panel">
          <div class="section-heading">
            <h2>Inspection history</h2>
            <FieldIcon name="clock" />
          </div>
          <p v-if="!jobInspections.length" class="muted">
            Your inspections and corrections will appear here.
          </p>
          <button
            v-for="record in jobInspections"
            :key="record.name"
            class="history-row"
            @click="openInspection(record.name)"
          >
            <span
              class="history-icon"
              :class="{ green: record.inspection_status === 'Completed' }"
              ><FieldIcon
                :name="
                  record.inspection_status === 'Completed'
                    ? 'check-circle'
                    : 'edit-3'
                " /></span
            ><span
              ><strong>{{ stageLabel(record.inspection_stage) }}</strong
              ><small
                >{{ record.name
                }}<template v-if="record.corrects_inspection">
                  · Correction of {{ record.corrects_inspection }}</template
                ></small
              ></span
            ><span
              class="status-tag"
              :class="{ complete: record.inspection_status === 'Completed' }"
              >{{ record.inspection_status }}</span
            ><FieldIcon name="chevron-right" />
          </button>
        </div>
        <a
          v-if="hasDesk"
          class="button secondary desk-link"
          :href="
            '/app/service-job-card/' + encodeURIComponent(selectedJob.name)
          "
          ><FieldIcon name="external-link" />Open Job Card in Desk</a
        >
      </section>

      <section v-else-if="screen === 'template'" class="template-page">
        <button class="back" @click="screen = 'job'">
          <FieldIcon name="arrow-left" />Back to Job Card
        </button>
        <div class="headline">
          <div>
            <p class="eyebrow">
              {{ selectedJob.service_item_name }} · {{ selectedJob.name }}
            </p>
            <h1>Choose your checklist</h1>
            <p class="muted">
              {{ stageName }} · A configured template is required.
            </p>
          </div>
        </div>
        <div v-if="!templates.length" class="empty">
          No accessible templates for this stage. Ask your manager to configure
          a template.
        </div>
        <button
          v-for="item in templates"
          :key="item.name"
          class="template-choice"
          :disabled="busy || !online"
          @click="startInspection(item.name)"
        >
          <span class="stat-icon"><FieldIcon name="clipboard" /></span
          ><span
            ><strong>{{ item.template_name || item.name }}</strong
            ><small>{{
              item.require_photographs
                ? 'Stage photograph required'
                : 'Stage photographs optional'
            }}</small></span
          ><FieldIcon name="chevron-right" />
        </button>
      </section>

      <section
        v-else-if="screen === 'inspection' && inspection"
        class="inspection-page"
      >
        <InspectionWizard
          :inspection="inspection"
          :job="selectedJob"
          :checklist="checklist"
          :values="values"
          :photos="photos"
          :online="online"
          :busy="busy"
          :uploading="uploading"
          :upload-progress="uploadProgress"
          :gps-busy="gpsBusy"
          :gps-message="gpsMessage"
          :status-message="statusMessage"
          :failed-upload="failedUpload?.message || ''"
          @back="returnToJob"
          @save="saveDraft"
          @complete="completeInspection"
          @upload="pickPhoto"
          @retry="retryUpload"
          @gps="captureGPS"
          @correction="correctionOpen = !correctionOpen"
        >
          <template #correction
            ><form
              v-if="correctionOpen"
              class="correction-form"
              @submit.prevent="createCorrection"
            >
              <label class="field-label"
                >Correction reason<textarea
                  v-model="correctionReason"
                  class="field-input"
                  required
                  maxlength="1000"
                  :disabled="busy"
                  rows="3"
                ></textarea></label
              ><button
                class="button primary"
                type="submit"
                :disabled="busy || !online || !correctionReason.trim()"
              >
                Start correction<FieldIcon name="arrow-right" />
              </button></form
          ></template>
        </InspectionWizard>
      </section>

      <section v-else-if="screen === 'complete'" class="completion-page">
        <div class="completion-orbit"><FieldIcon name="check" /></div>
        <p class="eyebrow">ALL SET. WELL DOCUMENTED.</p>
        <h1>Inspection complete</h1>
        <p class="muted">
          Your inspection has been saved and protected.<br />It is now part of
          the vehicle's history.
        </p>
        <div class="panel completion-receipt">
          <span class="status-tag complete">Completed</span>
          <h2>{{ selectedJob.service_item_name }}</h2>
          <dl>
            <div>
              <dt>Inspection</dt>
              <dd>{{ inspection.name }}</dd>
            </div>
            <div>
              <dt>Job Card</dt>
              <dd>{{ selectedJob.name }}</dd>
            </div>
            <div>
              <dt>Stage</dt>
              <dd>{{ stageLabel(inspection.inspection_stage) }}</dd>
            </div>
            <div>
              <dt>Completed at</dt>
              <dd>{{ formatCaptureTime(inspection.inspected_on) }}</dd>
            </div>
          </dl>
        </div>
        <button class="button primary" @click="screen = 'inspection'">
          <FieldIcon name="eye" />View Inspection</button
        ><button class="button secondary" @click="returnToJob">
          Return to Job Card<FieldIcon name="arrow-right" />
        </button>
      </section>

      <section v-else-if="screen === 'history'" class="history-page">
        <div class="headline">
          <div>
            <p class="eyebrow">YOUR INSPECTION RECORD</p>
            <h1>Inspections</h1>
            <p class="muted">Resume drafts or review completed work.</p>
          </div>
          <button
            class="icon-button subtle"
            aria-label="Refresh history"
            :disabled="historyLoading"
            @click="loadJobs"
          >
            <FieldIcon name="refresh-cw" />
          </button>
        </div>
        <div class="filter-tabs history-filters">
          <button
            v-for="filter in ['All', 'Draft', 'Completed']"
            :key="filter"
            :class="{ active: historyFilter === filter }"
            @click="historyFilter = filter"
          >
            {{ filter }}
          </button>
        </div>
        <div v-if="historyLoading" class="empty">
          Loading accessible inspection history…
        </div>
        <div v-else-if="!filteredHistory.length" class="empty">
          <FieldIcon name="clipboard" />
          <h3>No inspections to show</h3>
          <p>Inspections for your accessible Job Cards will appear here.</p>
        </div>
        <div v-else class="panel history-panel">
          <button
            v-for="record in filteredHistory"
            :key="record.name"
            class="history-row"
            @click="openHistory(record)"
          >
            <span
              class="history-icon"
              :class="{ green: record.inspection_status === 'Completed' }"
              ><FieldIcon
                :name="
                  record.inspection_status === 'Completed'
                    ? 'check-circle'
                    : 'edit-3'
                " /></span
            ><span
              ><strong>{{ record.job.service_item_name }}</strong
              ><small
                >{{ stageLabel(record.inspection_stage) }} ·
                {{ record.name }}</small
              ><small
                >{{ record.job.name }} · {{ record.job.workshop }}</small
              ></span
            ><span
              class="status-tag"
              :class="{ complete: record.inspection_status === 'Completed' }"
              >{{ record.inspection_status }}</span
            ><FieldIcon name="chevron-right" />
          </button>
        </div>
      </section>

      <section v-else-if="screen === 'account'" class="account-page">
        <p class="eyebrow">SERVICEMS FIELD</p>
        <h1>Your account</h1>
        <div class="panel account-card">
          <span class="account-avatar">{{
            fieldUser.slice(0, 1).toUpperCase()
          }}</span>
          <h2>Signed in as</h2>
          <p>{{ fieldUser }}</p>
          <span class="status-tag" :class="{ complete: online }">{{
            online ? 'Connected' : 'Offline'
          }}</span>
        </div>
        <div class="panel account-actions">
          <button @click="darkMode = !darkMode">
            <FieldIcon :name="darkMode ? 'sun' : 'moon'" /><span>{{
              darkMode ? 'Switch to light mode' : 'Switch to dark mode'
            }}</span
            ><FieldIcon name="chevron-right" /></button
          ><a v-if="hasDesk" href="/app/service-ms"
            ><FieldIcon name="external-link" /><span>Open Frappe Desk</span
            ><FieldIcon name="chevron-right" /></a
          ><button :disabled="navigationLocked" @click="signOut">
            <FieldIcon name="log-out" /><span>Sign out</span
            ><FieldIcon name="chevron-right" />
          </button>
        </div>
        <p class="muted compact-note">
          An internet connection is required to load and save inspections. Your
          account permissions determine which Job Cards you can access.
        </p>
      </section>
    </main>
    <nav class="bottom-nav" aria-label="Field navigation">
      <button
        :class="{ active: !['history', 'account'].includes(screen) }"
        :disabled="navigationLocked"
        @click="navigate('jobs')"
      >
        <FieldIcon name="grid" /><span>Home</span></button
      ><button
        :class="{ active: screen === 'history' }"
        :disabled="navigationLocked"
        @click="navigate('history')"
      >
        <FieldIcon name="clipboard" /><span>Inspections</span></button
      ><button
        :class="{ active: screen === 'account' }"
        :disabled="navigationLocked"
        @click="navigate('account')"
      >
        <FieldIcon name="user" /><span>Account</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { api, uploadPhoto } from './api'
import FieldIcon from './FieldIcon.vue'
import InspectionWizard from './InspectionWizard.vue'
import {
  formatCaptureTime,
  loadJobHistories,
  stageRecord,
} from './inspectionUi'

const screen = ref('jobs')
const fieldUser = window.field_user || ''
const hasDesk = window.field_has_desk === true
const histories = ref({})
const historyLoading = ref(false)
const historyErrors = ref([])
const jobSearch = ref('')
const jobFilter = ref('All')
const historyFilter = ref('All')
const failedUpload = ref(null)
const navigationLocked = computed(
  () => busy.value || uploading.value || gpsBusy.value
)
const allInspections = computed(() =>
  jobs.value
    .flatMap((job) =>
      (histories.value[job.name] || []).map((record) => ({ ...record, job }))
    )
    .sort((a, b) => String(b.modified).localeCompare(String(a.modified)))
)
const nextDraft = computed(() =>
  allInspections.value.find((record) => record.inspection_status === 'Draft')
)
const filteredHistory = computed(() =>
  allInspections.value.filter(
    (record) =>
      historyFilter.value === 'All' ||
      record.inspection_status === historyFilter.value
  )
)
const filteredJobs = computed(() =>
  jobs.value.filter(
    (job) =>
      [job.name, job.service_item_name, job.vehicle_model, job.workshop]
        .join(' ')
        .toLowerCase()
        .includes(jobSearch.value.toLowerCase()) &&
      (jobFilter.value === 'All' ||
        (histories.value[job.name] || []).some(
          (record) => record.inspection_status === jobFilter.value
        ))
  )
)
const online = ref(navigator.onLine)
const darkMode = ref(
  window.matchMedia?.('(prefers-color-scheme: dark)').matches || false
)
const jobs = ref([])
const jobInspections = ref([])
const selectedJob = ref(null)
const stage = ref('Pre-Service')
const templates = ref([])
const inspection = ref(null)
const checklist = ref([])
const photos = ref([])
const values = ref({})
const loading = ref(false)
const busy = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const error = ref('')
const statusMessage = ref('')
const gpsMessage = ref('')
const gpsBusy = ref(false)
const correctionOpen = ref(false)
const correctionReason = ref('')
const savedDraft = ref('')
let gpsRequest = 0
const draftSignature = () => JSON.stringify([values.value, checklist.value])
const dirty = computed(
  () =>
    screen.value === 'inspection' &&
    inspection.value &&
    !completed.value &&
    ((savedDraft.value && draftSignature() !== savedDraft.value) ||
      failedUpload.value)
)
const stages = ['Pre-Service', 'Post-Service']
const completed = computed(
  () => inspection.value?.inspection_status === 'Completed'
)
const stageName = computed(() =>
  stage.value === 'Pre-Service' ? 'Pre-Inspection' : 'Post-Inspection'
)

function connected() {
  online.value = navigator.onLine
}
function warnUnsaved(event) {
  if (!dirty.value && !uploading.value) return
  event.preventDefault()
  event.returnValue = ''
}
function stageLabel(stage) {
  return stage === 'Pre-Service' ? 'Pre-Inspection' : 'Post-Inspection'
}
function showCompletedHistory() {
  historyFilter.value = 'Completed'
  navigate('history')
}
function stageStatus(job, stage) {
  return (
    stageRecord(histories.value[job] || [], stage)?.inspection_status ||
    (historyErrors.value.includes(job)
      ? 'Unavailable'
      : historyLoading.value
      ? 'Loading…'
      : 'Not started')
  )
}
function stageClass(job, stage) {
  return {
    complete: stageStatus(job, stage) === 'Completed',
    draft: stageStatus(job, stage) === 'Draft',
  }
}
async function navigate(next) {
  if (navigationLocked.value) return
  if (
    dirty.value &&
    !window.confirm(
      'Discard unsaved inspection changes? Save Draft first to keep them.'
    )
  )
    return
  screen.value = next
  window.scrollTo({ top: 0, behavior: 'instant' })
}
async function openHistory(record) {
  if (await openJob(record.job)) await openInspection(record.name)
}
onMounted(() => {
  addEventListener('online', connected)
  addEventListener('offline', connected)
  addEventListener('beforeunload', warnUnsaved)
  loadJobs().then(async () => {
    const jobCard = new URLSearchParams(window.location.search).get('job_card')
    if (jobCard) {
      const job = await invoke(() =>
        api('servicems.field_api.get_field_job', { job_card: jobCard })
      )
      if (job) await openJob(job)
    }
  })
})
onBeforeUnmount(() => {
  removeEventListener('online', connected)
  removeEventListener('offline', connected)
  removeEventListener('beforeunload', warnUnsaved)
})
async function invoke(action) {
  error.value = ''
  try {
    return await action()
  } catch (e) {
    error.value = e.message || String(e)
    return null
  }
}
async function signOut() {
  if (
    (dirty.value || uploading.value) &&
    !window.confirm('Sign out and discard unsaved changes?')
  )
    return
  busy.value = true
  try {
    await api('logout', {}, true)
    removeEventListener('beforeunload', warnUnsaved)
    window.location.replace('/field')
  } catch (e) {
    error.value = e.message || String(e)
    busy.value = false
  }
}
async function loadJobs() {
  loading.value = true
  await invoke(async () => {
    jobs.value = await api('servicems.field_api.get_field_jobs', { limit: 100 })
    historyLoading.value = true
    const result = await loadJobHistories(jobs.value, (name) =>
      api('servicems.field_api.get_job_inspections', { job_card: name })
    )
    histories.value = result.records
    historyErrors.value = result.errors
    historyLoading.value = false
  })
  loading.value = false
}
async function openJob(job) {
  const list = await invoke(() =>
    api('servicems.field_api.get_job_inspections', { job_card: job.name })
  )
  if (list) {
    selectedJob.value = job
    jobInspections.value = list
    histories.value = { ...histories.value, [job.name]: list }
    screen.value = 'job'
    window.scrollTo({ top: 0, behavior: 'instant' })
    return true
  }
  return false
}
async function chooseTemplate(nextStage) {
  stage.value = nextStage
  const list = await invoke(() =>
    api('servicems.field_api.get_inspection_templates', { stage: nextStage })
  )
  if (list) {
    templates.value = list
    screen.value = 'template'
  }
}
async function startInspection(template) {
  if (!online.value) return
  busy.value = true
  const record = await invoke(() =>
    api(
      'servicems.field_api.start_inspection',
      { job_card: selectedJob.value.name, stage: stage.value, template },
      true
    )
  )
  busy.value = false
  if (record) await openInspection(record.name)
}
async function openInspection(name) {
  const record = await invoke(() =>
    api('servicems.field_api.get_field_inspection', { name })
  )
  if (!record) return
  inspection.value = record
  const records = histories.value[record.service_job_card] || []
  histories.value = {
    ...histories.value,
    [record.service_job_card]: [
      record,
      ...records.filter((item) => item.name !== record.name),
    ],
  }
  failedUpload.value = null
  gpsRequest++
  gpsBusy.value = false
  gpsMessage.value = ''
  statusMessage.value = ''
  correctionOpen.value = false
  correctionReason.value = ''
  checklist.value = (record.checklist || []).map((row) => ({ ...row }))
  values.value = {
    inspection_remarks: record.inspection_remarks || '',
    mileage: record.mileage || '',
    gps_latitude: record.gps_captured_at ? record.gps_latitude : null,
    gps_longitude: record.gps_captured_at ? record.gps_longitude : null,
    gps_accuracy: record.gps_captured_at ? record.gps_accuracy : null,
    gps_captured_at: record.gps_captured_at ?? null,
    image_upload: record.image_upload || '',
  }
  photos.value = []
  savedDraft.value = draftSignature()
  await refreshPhotos()
  screen.value = 'inspection'
}
async function refreshPhotos() {
  if (!inspection.value) return
  // File metadata is queried under ordinary Frappe read permissions.
  const items = await invoke(() =>
    api('servicems.field_api.get_inspection_photos', {
      name: inspection.value.name,
    })
  )
  if (items) photos.value = items
}
async function returnToJob() {
  if (busy.value || uploading.value || gpsBusy.value) return
  if (
    dirty.value &&
    !window.confirm(
      'Discard unsaved inspection changes? Save Draft first to keep them.'
    )
  )
    return
  if (selectedJob.value) await openJob(selectedJob.value)
  else screen.value = 'jobs'
}
async function pickPhoto(event, row) {
  const files = [...(event.target.files || [])]
  event.target.value = ''
  await uploadFiles(files, row)
}
async function retryUpload() {
  if (failedUpload.value)
    await uploadFiles(failedUpload.value.files, failedUpload.value.row)
}
async function uploadFiles(files, row) {
  if (
    !files.length ||
    !inspection.value ||
    completed.value ||
    !online.value ||
    navigationLocked.value
  )
    return
  uploading.value = true
  failedUpload.value = null
  error.value = ''
  let index = 0
  try {
    for (; index < files.length; index++) {
      const file = files[index]
      if (!file.type.startsWith('image/'))
        throw new Error('Only photographs are accepted.')
      if (file.size > 10 * 1024 * 1024)
        throw new Error('Photographs must be 10 MB or smaller.')
      uploadProgress.value = 0
      const saved = await uploadPhoto(
        file,
        inspection.value.name,
        (n) => (uploadProgress.value = n)
      )
      if (row) row.photograph = saved.file_url
      else if (!values.value.image_upload)
        values.value.image_upload = saved.file_url
    }
    statusMessage.value =
      'Photos uploaded privately. Save Draft to retain selected photo references.'
  } catch (e) {
    failedUpload.value = { files: files.slice(index), row, message: e.message }
    error.value = e.message
  } finally {
    await refreshPhotos()
    uploading.value = false
    uploadProgress.value = 0
  }
}
function captureGPS() {
  if (gpsBusy.value || completed.value) return
  if (!navigator.geolocation) {
    gpsMessage.value = 'GPS is unavailable on this device.'
    return
  }
  gpsMessage.value = 'Requesting location permission…'
  gpsBusy.value = true
  const request = ++gpsRequest
  const name = inspection.value.name
  navigator.geolocation.getCurrentPosition(
    ({ coords, timestamp }) => {
      if (
        request !== gpsRequest ||
        inspection.value.name !== name ||
        completed.value
      )
        return
      gpsBusy.value = false
      values.value.gps_latitude = coords.latitude
      values.value.gps_longitude = coords.longitude
      values.value.gps_accuracy = coords.accuracy
      const date = new Date(timestamp)
      values.value.gps_captured_at = date.toISOString()
      gpsMessage.value =
        'Location captured with your permission. Save Draft to retain it on the server.'
    },
    (e) => {
      if (request !== gpsRequest) return
      gpsBusy.value = false
      gpsMessage.value =
        e.code === 1
          ? 'Location access denied. Update browser permissions to try again.'
          : 'Could not obtain a reliable location. Please retry.'
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
  )
}
function payload() {
  return {
    name: inspection.value.name,
    expected_modified: inspection.value.modified,
    values: { ...values.value },
    answers: checklist.value.map((r) => ({
      name: r.name,
      answer: r.answer || '',
      remarks: r.remarks || '',
      photograph: r.photograph || '',
    })),
  }
}
async function saveDraft() {
  if (!online.value || busy.value || completed.value) return false
  busy.value = true
  const success = await invoke(() =>
    api('servicems.field_api.save_field_draft', payload(), true)
  )
  busy.value = false
  if (!success) return false
  inspection.value.modified = success.modified
  savedDraft.value = draftSignature()
  statusMessage.value = 'Draft saved on server.'
  return true
}
async function createCorrection() {
  if (busy.value || !online.value || !correctionReason.value.trim()) return
  busy.value = true
  const result = await invoke(() =>
    api(
      'servicems.field_api.create_field_correction',
      { name: inspection.value.name, reason: correctionReason.value.trim() },
      true
    )
  )
  busy.value = false
  if (result) await openInspection(result.name)
}
async function completeInspection() {
  if (!(await saveDraft())) return
  busy.value = true
  const saved = await invoke(() =>
    api(
      'servicems.field_api.complete_field_inspection',
      { name: inspection.value.name },
      true
    )
  )
  busy.value = false
  if (saved) {
    await openInspection(inspection.value.name)
    if (inspection.value.inspection_status === 'Completed') {
      screen.value = 'complete'
      statusMessage.value = 'Inspection completed and protected.'
    }
  }
}
</script>
