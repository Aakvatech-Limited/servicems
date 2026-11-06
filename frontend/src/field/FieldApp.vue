<template>
  <div class="field-app" :class="{ 'field-dark': darkMode }">
    <header class="field-header">
      <div class="field-brand">
        <span class="field-logo">S</span
        ><span>ServiceMS <strong>Field</strong></span>
      </div>
      <div class="field-header-actions">
        <span class="connection" :class="{ offline: !online }">{{
          online ? 'Online' : 'Offline — view only'
        }}</span>
        <button
          class="icon-button"
          type="button"
          :aria-label="darkMode ? 'Light theme' : 'Dark theme'"
          @click="darkMode = !darkMode"
        >
          {{ darkMode ? '☀' : '☾' }}
        </button>
        <a class="icon-button" href="/app/service-ms" aria-label="Frappe Desk"
          >⌂</a
        >
      </div>
    </header>

    <main class="field-main">
      <div v-if="error" class="alert error" role="alert">
        {{ error }} <button type="button" @click="error = ''">Dismiss</button>
      </div>

      <section v-if="screen === 'jobs'" aria-label="Accessible job cards">
        <div class="headline">
          <div>
            <p class="eyebrow">FIELD OPERATIONS</p>
            <h1>My Job Cards</h1>
            <p class="muted">
              Select a Job Card to begin or resume an inspection.
            </p>
          </div>
          <button class="button secondary" type="button" @click="loadJobs">
            ↻ Refresh
          </button>
        </div>
        <div v-if="loading" class="empty" role="status">
          Loading accessible Job Cards…
        </div>
        <div v-else-if="!jobs.length" class="empty">
          No accessible Job Cards. Ask your manager to verify your permissions
          or assignments.
        </div>
        <div v-else class="job-grid">
          <button
            v-for="job in jobs"
            :key="job.name"
            class="job-card"
            @click="openJob(job)"
            type="button"
          >
            <span class="job-head"
              ><strong>{{ job.name }}</strong
              ><span class="status-tag">{{ job.status }}</span></span
            >
            <span class="vehicle-title">{{
              job.vehicle_model || job.service_item_name
            }}</span>
            <span class="muted"
              >{{ job.service_item_name }} · {{ job.workshop }}</span
            >
            <span class="job-footer"
              >Inspect vehicle <span aria-hidden="true">›</span></span
            >
          </button>
        </div>
      </section>

      <section v-else-if="screen === 'job'" aria-label="Selected Job Card">
        <button class="back" type="button" @click="screen = 'jobs'">
          ‹ All Job Cards
        </button>
        <div class="headline">
          <div>
            <p class="eyebrow">JOB CARD</p>
            <h1>{{ selectedJob.name }}</h1>
            <p class="muted">
              {{ selectedJob.vehicle_model || selectedJob.service_item_name }} ·
              {{ selectedJob.workshop }}
            </p>
          </div>
          <a
            class="button secondary"
            :href="
              '/app/service-job-card/' + encodeURIComponent(selectedJob.name)
            "
            >Desk record</a
          >
        </div>
        <div class="stage-grid">
          <div v-for="stage in stages" :key="stage" class="stage-card">
            <h2>
              {{
                stage === 'Pre-Service' ? 'Pre-Inspection' : 'Post-Inspection'
              }}
            </h2>
            <p class="muted">Template-driven checklist, photos and findings.</p>
            <button
              v-if="online"
              class="button primary"
              type="button"
              @click="chooseTemplate(stage)"
            >
              + Start {{ stage === 'Pre-Service' ? 'Pre' : 'Post' }}
            </button>
            <p v-else class="muted">Connection required to start.</p>
            <button
              v-for="record in jobInspections.filter(
                (i) => i.inspection_stage === stage
              )"
              :key="record.name"
              class="inspection-link"
              type="button"
              @click="openInspection(record.name)"
            >
              <span>{{ record.name }}</span
              ><span class="status-tag">{{ record.inspection_status }}</span>
            </button>
          </div>
        </div>
      </section>

      <section v-else-if="screen === 'template'" class="form-page">
        <button class="back" type="button" @click="screen = 'job'">
          ‹ Back to Job Card
        </button>
        <div class="headline">
          <div>
            <p class="eyebrow">{{ selectedJob.name }}</p>
            <h1>Choose {{ stageName }} Template</h1>
            <p class="muted">
              A template is mandatory for every new inspection.
            </p>
          </div>
        </div>
        <div v-if="!templates.length" class="empty">
          No accessible templates for this stage. A manager must configure a
          template first.
        </div>
        <button
          v-for="item in templates"
          :key="item.name"
          class="template-choice"
          type="button"
          :disabled="busy || !online"
          @click="startInspection(item.name)"
        >
          <span
            ><strong>{{ item.template_name || item.name }}</strong
            ><small>{{
              item.require_photographs
                ? 'Stage photo required'
                : 'Photos optional at stage level'
            }}</small></span
          ><span aria-hidden="true">›</span>
        </button>
      </section>

      <section
        v-else-if="screen === 'inspection' && inspection"
        class="inspection-page"
      >
        <button class="back" type="button" @click="returnToJob">
          ‹ {{ selectedJob.name }}
        </button>
        <div class="headline">
          <div>
            <p class="eyebrow">
              {{ inspection.inspection_stage }} · {{ selectedJob.name }}
            </p>
            <h1>Vehicle Inspection</h1>
            <p class="muted">
              {{ inspection.inspection_template }} · {{ inspection.name }}
            </p>
          </div>
          <span class="status-tag" :class="{ complete: completed }">{{
            inspection.inspection_status
          }}</span>
        </div>
        <div class="progress-panel">
          <div>
            <strong>{{ answeredCount }} / {{ checklist.length }}</strong>
            checklist answers
            <span class="muted">· Required answers checked on completion</span>
          </div>
          <div class="progress-track">
            <div
              class="progress-value"
              :style="{ width: completionPercent + '%' }"
            ></div>
          </div>
        </div>
        <div class="inspection-layout">
          <div class="inspection-body">
            <section class="panel">
              <h2>Inspection checklist</h2>
              <p class="muted">
                Select a condition and record findings. Required items are
                marked *.
              </p>
              <div v-if="!checklist.length" class="empty">
                No checklist items in this template.
              </div>
              <div
                v-for="(row, index) in checklist"
                :key="row.name"
                class="checklist-row"
              >
                <div class="item-title">
                  <span class="item-index">{{ index + 1 }}</span
                  ><strong
                    >{{ row.inspection_item }}
                    <span v-if="row.is_required" class="required"
                      >*</span
                    ></strong
                  >
                </div>
                <div
                  v-if="row.inspection_type === 'Check'"
                  class="answer-controls"
                >
                  <label
                    v-for="choice in answerChoices(row)"
                    :key="choice"
                    class="answer-chip"
                    :class="{ chosen: row.answer === choice }"
                    ><input
                      v-model="row.answer"
                      type="radio"
                      :name="'answer-' + row.name"
                      :value="choice"
                      :disabled="completed || busy"
                    />{{ choice }}</label
                  >
                </div>
                <label v-else class="field-label"
                  >Condition / Answer
                  <input
                    v-model="row.answer"
                    class="field-input"
                    type="text"
                    :disabled="completed || busy"
                    :placeholder="row.option || 'Enter finding'"
                  />
                </label>
                <label class="field-label"
                  >Remarks
                  <textarea
                    v-model="row.remarks"
                    class="field-input"
                    rows="2"
                    :disabled="completed || busy"
                    placeholder="Optional observations"
                  ></textarea>
                </label>
                <div class="item-photos">
                  <span class="muted">{{
                    row.require_photo ? 'Photo required *' : 'Photo optional'
                  }}</span>
                  <span v-if="row.photograph" class="saved-photo"
                    >✓ Photo saved</span
                  >
                  <label
                    v-if="!completed && online"
                    class="button secondary small"
                    >📷 Add photo
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      hidden
                      :disabled="busy || uploading"
                      @change="pickPhoto($event, row)"
                    />
                  </label>
                </div>
              </div>
            </section>
          </div>

          <aside class="inspection-aside">
            <section class="panel">
              <h2>Photo evidence</h2>
              <p class="muted">
                {{
                  inspection.require_photographs_snapshot
                    ? 'At least one stage photograph required.'
                    : 'Stage photographs optional.'
                }}
                Per-item requirements still apply.
              </p>
              <div class="photo-grid">
                <a
                  v-for="photo in photos"
                  :key="photo.name"
                  :href="photo.file_url"
                  target="_blank"
                  rel="noopener"
                  class="photo-thumb"
                  ><img
                    :src="photo.file_url"
                    :alt="photo.file_name || 'Inspection photo'"
                    loading="lazy"
                  />
                  <span>{{ photo.file_name || 'View photo' }}</span></a
                >
              </div>
              <div v-if="!completed && online" class="photo-actions">
                <label class="button secondary photo-picker"
                  >📷 Camera
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    hidden
                    :disabled="busy || uploading"
                    @change="pickPhoto($event, null)"
                  />
                </label>
                <label class="button secondary photo-picker"
                  >▧ Photo library
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    hidden
                    :disabled="busy || uploading"
                    @change="pickPhoto($event, null)"
                  />
                </label>
              </div>
              <div v-if="uploading" role="status">
                Uploading private photo: {{ uploadProgress }}%
              </div>
            </section>
            <section class="panel">
              <h2>Findings & details</h2>
              <label class="field-label"
                >Inspection remarks
                <textarea
                  v-model="values.inspection_remarks"
                  :disabled="completed || busy"
                  rows="4"
                  class="field-input"
                  placeholder="Damage, observations or recommendations"
                ></textarea>
              </label>
              <label class="field-label"
                >Mileage
                <input
                  v-model="values.mileage"
                  type="text"
                  :disabled="completed || busy"
                  class="field-input"
                />
              </label>
            </section>
            <section class="panel">
              <h2>Location (GPS)</h2>
              <p class="muted">
                {{
                  inspection.require_gps_snapshot
                    ? 'Required by template.'
                    : 'Optional on this inspection.'
                }}
              </p>
              <div
                v-if="
                  values.gps_latitude !== null &&
                  values.gps_latitude !== undefined
                "
                class="location-result"
              >
                ✓ {{ Number(values.gps_latitude).toFixed(5) }},
                {{ Number(values.gps_longitude).toFixed(5) }}
                <small>Accuracy: {{ values.gps_accuracy }} m</small>
              </div>
              <p v-if="gpsMessage" class="muted" role="status">
                {{ gpsMessage }}
              </p>
              <button
                v-if="!completed"
                class="button secondary"
                type="button"
                :disabled="!online || busy || gpsBusy"
                @click="captureGPS"
              >
                📍
                {{
                  values.gps_latitude == null
                    ? 'Capture GPS'
                    : 'Refresh location'
                }}
              </button>
            </section>
          </aside>
        </div>
        <div class="action-bar">
          <span v-if="!online" class="muted"
            >Offline — changes cannot be saved yet.</span
          >
          <span v-else-if="statusMessage" class="muted" role="status">{{
            statusMessage
          }}</span>
          <template v-if="!completed">
            <button
              class="button secondary"
              type="button"
              :disabled="busy || !online || uploading || gpsBusy"
              @click="saveDraft"
            >
              Save Draft
            </button>
            <button
              class="button primary"
              type="button"
              :disabled="busy || !online || uploading || gpsBusy"
              @click="completeInspection"
            >
              Complete Inspection
            </button>
          </template>
          <template v-else>
            <button
              class="button secondary"
              type="button"
              :disabled="busy || !online"
              @click="correctionOpen = !correctionOpen"
            >
              Create correction
            </button>
            <button class="button primary" type="button" @click="returnToJob">
              Return to Job Card
            </button>
          </template>
        </div>
        <form
          v-if="completed && correctionOpen"
          class="panel correction-form"
          @submit.prevent="createCorrection"
        >
          <label class="field-label"
            >Correction reason
            <textarea
              v-model="correctionReason"
              class="field-input"
              required
              maxlength="1000"
              :disabled="busy"
              rows="3"
            ></textarea>
          </label>
          <button
            class="button primary"
            type="submit"
            :disabled="busy || !online || !correctionReason.trim()"
          >
            Start correction
          </button>
        </form>
      </section>
    </main>
    <footer class="field-footer">
      <span>ServiceMS Field Operations · Online inspections</span
      ><span>No offline record storage</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { api, uploadPhoto } from './api'

const screen = ref('jobs')
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
    inspection.value &&
    !completed.value &&
    savedDraft.value &&
    draftSignature() !== savedDraft.value
)
const stages = ['Pre-Service', 'Post-Service']
const completed = computed(
  () => inspection.value?.inspection_status === 'Completed'
)
const answeredCount = computed(
  () => checklist.value.filter((r) => String(r.answer || '').trim()).length
)
const completionPercent = computed(() =>
  checklist.value.length
    ? Math.round((answeredCount.value / checklist.value.length) * 100)
    : 0
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
function answerChoices(row) {
  const choices = row.option
    ?.split(/\r?\n/)
    .map((value) => value.trim())
    .filter(Boolean)
  return choices?.length ? choices : ['Yes', 'No', 'N/A']
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
async function loadJobs() {
  loading.value = true
  await invoke(async () => {
    jobs.value = await api('servicems.field_api.get_field_jobs')
    screen.value = 'jobs'
  })
  loading.value = false
}
async function openJob(job) {
  selectedJob.value = job
  const list = await invoke(() =>
    api('servicems.field_api.get_job_inspections', { job_card: job.name })
  )
  if (list) {
    jobInspections.value = list
    screen.value = 'job'
  }
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
  if (!files.length || !inspection.value || completed.value || !online.value)
    return
  uploading.value = true
  try {
    for (const file of files) {
      if (!file.type.startsWith('image/'))
        throw new Error('Only photographs are accepted.')
      if (file.size > 10 * 1024 * 1024)
        throw new Error('Photographs must be 10 MB or smaller.')
      const saved = await uploadPhoto(
        file,
        inspection.value.name,
        (n) => (uploadProgress.value = n)
      )
      if (row) row.photograph = saved.file_url
      else if (!values.value.image_upload)
        values.value.image_upload = saved.file_url
    }
    await refreshPhotos()
    statusMessage.value =
      'Photos uploaded privately. Save Draft to link selected photo references.'
  } catch (e) {
    error.value = e.message
  } finally {
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
    inspection.value.inspection_status = 'Completed'
    statusMessage.value = 'Inspection completed and protected.'
  }
}
</script>
