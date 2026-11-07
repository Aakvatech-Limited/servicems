<template>
  <div class="guided-inspection">
    <div class="wizard-heading">
      <button
        class="icon-button back-button"
        aria-label="Return to Job Card"
        :disabled="locked"
        @click="$emit('back')"
      >
        <FieldIcon name="arrow-left" />
      </button>
      <div>
        <p class="eyebrow">{{ stageLabel }} · {{ inspection.name }}</p>
        <h1>
          {{
            steps[step].title === 'Vehicle'
              ? 'Start with your vehicle'
              : titles[step]
          }}
        </h1>
      </div>
      <span class="status-tag" :class="{ complete: completed }">{{
        inspection.inspection_status
      }}</span>
    </div>
    <div v-if="completed" class="notice success">
      <FieldIcon name="shield" /> Completed inspections are read-only. Use a
      correction to record changes.
    </div>
    <div class="wizard-layout">
      <nav class="step-nav" aria-label="Inspection sections">
        <div class="step-progress">
          <span>INSPECTION PROGRESS</span><strong>{{ step + 1 }} of 5</strong>
        </div>
        <button
          v-for="(item, index) in steps"
          :key="item.title"
          :data-step="index"
          :class="{
            active: step === index,
            visited:
              index < step && !issues.some((issue) => issue.step === index),
          }"
          :aria-current="step === index ? 'step' : undefined"
          @click="move(index)"
        >
          <span class="step-number"
            ><FieldIcon
              v-if="
                index < step && !issues.some((issue) => issue.step === index)
              "
              name="check"
            /><span v-else>{{ index + 1 }}</span></span
          ><span class="step-label">{{ item.title }}</span
          ><FieldIcon class="step-chevron" name="chevron-right" />
        </button>
        <div class="step-summary">
          <FieldIcon name="truck" /><strong>{{ job.service_item_name }}</strong
          ><span>{{ job.vehicle_model || 'Vehicle inspection' }}</span
          ><small>{{ job.name }}</small>
        </div>
      </nav>

      <div class="wizard-content">
        <section v-show="step === 0" class="panel vehicle-overview">
          <span class="large-icon"><FieldIcon name="truck" /></span>
          <p class="eyebrow">VEHICLE & INSPECTION</p>
          <h2>{{ job.service_item_name }}</h2>
          <p class="muted">
            {{ job.vehicle_model || 'Vehicle' }} · {{ job.workshop }}
          </p>
          <dl class="detail-grid">
            <div>
              <dt>Job Card</dt>
              <dd>{{ job.name }}</dd>
            </div>
            <div>
              <dt>Stage</dt>
              <dd>{{ stageLabel }}</dd>
            </div>
            <div>
              <dt>Template</dt>
              <dd>{{ inspection.inspection_template }}</dd>
            </div>
            <div>
              <dt>Checklist</dt>
              <dd>{{ checklist.length }} items</dd>
            </div>
          </dl>
          <div class="requirement-list">
            <div>
              <FieldIcon name="camera" /><span
                >{{
                  inspection.require_photographs_snapshot
                    ? 'Stage photograph required'
                    : 'Stage photographs optional'
                }}<small
                  >Individual checklist photo requirements still apply.</small
                ></span
              >
            </div>
            <div>
              <FieldIcon name="map-pin" /><span
                >{{
                  inspection.require_gps_snapshot
                    ? 'GPS required by template'
                    : 'GPS optional'
                }}<small>Capture location only when you choose.</small></span
              >
            </div>
          </div>
          <p v-if="inspection.corrects_inspection" class="notice">
            Correction of {{ inspection.corrects_inspection }} ·
            {{ inspection.correction_reason }}
          </p>
        </section>

        <section v-show="step === 1" class="panel checklist-panel">
          <div class="section-heading">
            <div>
              <p class="eyebrow">CHECK THE VEHICLE</p>
              <h2>Inspection checklist</h2>
            </div>
            <span class="count-pill"
              >{{ answered }} / {{ checklist.length }}</span
            >
          </div>
          <div
            class="progress-track"
            :aria-label="answered + ' answered checklist items'"
          >
            <div
              :style="{
                width:
                  (checklist.length ? (answered / checklist.length) * 100 : 0) +
                  '%',
              }"
            ></div>
          </div>
          <p class="muted compact-note">
            Follow your template. Items marked * are required.
          </p>
          <p v-if="!checklist.length" class="empty">
            This template has no checklist items.
          </p>
          <article
            v-for="(row, index) in checklist"
            :key="row.name"
            class="checklist-row"
            :class="{ expanded: expanded === index }"
          >
            <button
              class="checklist-title"
              :aria-expanded="expanded === index"
              @click="expanded = expanded === index ? -1 : index"
            >
              <span class="item-index" :class="{ answered: row.answer }"
                ><FieldIcon v-if="row.answer" name="check" /><span v-else>{{
                  index + 1
                }}</span></span
              ><strong
                >{{ row.inspection_item
                }}<span v-if="row.is_required" class="required"> *</span
                ><small
                  >{{ row.answer || 'Choose a condition'
                  }}<template v-if="row.require_photo">
                    ·
                    {{
                      row.photograph ? 'Photo attached' : 'Photo required'
                    }}</template
                  ></small
                ></strong
              ><FieldIcon
                :name="expanded === index ? 'chevron-up' : 'chevron-down'"
              />
            </button>
            <div v-show="expanded === index" class="checklist-content">
              <div
                v-if="row.inspection_type === 'Check'"
                class="answer-controls"
                role="group"
                :aria-label="row.inspection_item"
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
                    :disabled="completed || locked"
                  /><FieldIcon v-if="row.answer === choice" name="check" />{{
                    choice
                  }}</label
                >
              </div>
              <label v-else class="field-label"
                >Condition / Answer<input
                  v-model="row.answer"
                  class="field-input"
                  :disabled="completed || locked"
                  :placeholder="row.option || 'Record the condition'"
              /></label>
              <label class="field-label"
                >Remarks <span class="optional">Optional</span
                ><textarea
                  v-model="row.remarks"
                  rows="2"
                  class="field-input"
                  :disabled="completed || locked"
                  placeholder="Add an observation"
                ></textarea>
              </label>
              <div class="item-photos">
                <span :class="row.photograph ? 'positive' : 'muted'"
                  ><FieldIcon
                    :name="row.photograph ? 'check-circle' : 'camera'"
                  />{{
                    row.photograph
                      ? 'Photo attached'
                      : row.require_photo
                      ? 'Photo required *'
                      : 'Photo optional'
                  }}</span
                ><label
                  v-if="!completed"
                  class="button secondary small photo-picker"
                  ><FieldIcon name="camera" />Add photo<input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    hidden
                    :disabled="locked || !online"
                    @change="$emit('upload', $event, row)"
                /></label>
              </div>
              <button
                v-if="index + 1 < checklist.length"
                class="text-button next-item"
                @click="expanded = index + 1"
              >
                Next item<FieldIcon name="arrow-right" />
              </button>
            </div>
          </article>
        </section>

        <section v-show="step === 2" class="evidence-section">
          <div class="panel capture-panel">
            <div class="section-heading">
              <div>
                <p class="eyebrow">A CLEAR PICTURE</p>
                <h2>Photographic evidence</h2>
              </div>
              <span class="count-pill">{{ photos.length }} photos</span>
            </div>
            <p class="muted">
              {{
                inspection.require_photographs_snapshot
                  ? 'Add at least one stage photograph.'
                  : 'Stage photographs are optional.'
              }}
              Capture details that support your inspection.
            </p>
            <div
              v-if="!completed"
              class="capture-area"
              :class="{ 'with-photos': photos.length }"
            >
              <span class="large-icon"><FieldIcon name="camera" /></span>
              <h3>Document what you see</h3>
              <p class="muted">
                Use your camera or choose multiple photographs.
              </p>
              <div class="photo-actions">
                <label class="button primary photo-picker"
                  ><FieldIcon name="camera" />Camera<input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    hidden
                    :disabled="locked || !online"
                    @change="$emit('upload', $event, null)" /></label
                ><label class="button secondary photo-picker"
                  ><FieldIcon name="image" />Photo library<input
                    type="file"
                    accept="image/*"
                    multiple
                    hidden
                    :disabled="locked || !online"
                    @change="$emit('upload', $event, null)"
                /></label>
              </div>
              <small class="muted"
                >Private photographs · Up to 10 MB per image</small
              >
            </div>
            <div v-if="uploading" class="upload-progress" role="status">
              <span>Uploading private photo: {{ uploadProgress }}%</span
              ><progress :value="uploadProgress" max="100"></progress>
            </div>
            <div v-if="failedUpload" class="notice danger" role="alert">
              <span>{{ failedUpload }}</span
              ><button
                class="button secondary small"
                :disabled="locked || !online"
                @click="$emit('retry')"
              >
                Retry upload
              </button>
            </div>
            <div v-if="requiredPhotos.length" class="required-photo-list">
              <h3>Checklist evidence</h3>
              <div v-for="row in requiredPhotos" :key="row.name">
                <span
                  ><FieldIcon
                    :name="row.photograph ? 'check-circle' : 'camera'"
                  />{{ row.inspection_item
                  }}<small>{{
                    row.photograph ? 'Photo attached' : 'Required *'
                  }}</small></span
                ><label
                  v-if="!completed"
                  class="button secondary small photo-picker"
                  >{{ row.photograph ? 'Replace' : 'Add photo'
                  }}<input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    hidden
                    :disabled="locked || !online"
                    @change="$emit('upload', $event, row)"
                /></label>
              </div>
            </div>
          </div>
          <div class="panel gallery-panel">
            <div class="section-heading">
              <h2>Your photographs</h2>
              <span class="muted">Tap to review</span>
            </div>
            <div v-if="photos.length" class="photo-grid">
              <button
                v-for="(photo, index) in photos"
                :key="photo.name"
                class="photo-thumb"
                @click="openPhoto(index)"
              >
                <img
                  :src="photo.file_url"
                  :alt="photo.file_name || 'Inspection photo'"
                  loading="lazy"
                /><span
                  ><FieldIcon name="maximize-2" />Photo {{ index + 1 }}</span
                >
              </button>
            </div>
            <p v-else class="empty">
              <FieldIcon name="image" />No photographs attached yet.
            </p>
          </div>
        </section>

        <section v-show="step === 3" class="findings-section">
          <div class="panel">
            <p class="eyebrow">LEAVE A CLEAR RECORD</p>
            <h2>Findings & observations</h2>
            <label class="field-label"
              >Inspection remarks<textarea
                v-model="values.inspection_remarks"
                class="field-input findings-text"
                rows="5"
                :disabled="completed || locked"
                placeholder="Record damage, observations or recommendations"
              ></textarea></label
            ><label class="field-label"
              >Mileage <span class="optional">Optional</span
              ><input
                v-model="values.mileage"
                class="field-input"
                :disabled="completed || locked"
                inputmode="decimal"
                placeholder="Vehicle mileage"
            /></label>
          </div>
          <div class="panel location-panel">
            <div class="section-heading">
              <span class="large-icon"><FieldIcon name="map-pin" /></span
              ><span class="count-pill">{{
                inspection.require_gps_snapshot ? 'Required *' : 'Optional'
              }}</span>
            </div>
            <h2>Inspection location</h2>
            <p class="muted">
              Capture a single location with your permission. Your location is
              not tracked continuously.
            </p>
            <div v-if="values.gps_captured_at" class="location-result">
              <FieldIcon name="check-circle" /><strong
                >Location captured</strong
              >
              <dl>
                <div>
                  <dt>Coordinates</dt>
                  <dd>
                    {{ Number(values.gps_latitude).toFixed(5) }},
                    {{ Number(values.gps_longitude).toFixed(5) }}
                  </dd>
                </div>
                <div>
                  <dt>Accuracy</dt>
                  <dd>{{ values.gps_accuracy }} m</dd>
                </div>
                <div>
                  <dt>Captured at</dt>
                  <dd>{{ formatCaptureTime(values.gps_captured_at) }}</dd>
                </div>
              </dl>
            </div>
            <p v-else class="location-empty">
              <FieldIcon name="navigation" />No location captured
            </p>
            <p v-if="gpsMessage" class="notice" role="status">
              {{ gpsMessage }}
            </p>
            <button
              v-if="!completed"
              class="button secondary"
              :disabled="locked || !online"
              @click="$emit('gps')"
            >
              <FieldIcon name="map-pin" />{{
                gpsBusy
                  ? 'Locating…'
                  : values.gps_captured_at
                  ? 'Refresh location'
                  : 'Capture GPS'
              }}
            </button>
          </div>
        </section>

        <section v-show="step === 4" class="review-section">
          <div class="panel review-heading">
            <span class="large-icon" :class="{ green: !issues.length }"
              ><FieldIcon :name="issues.length ? 'clipboard' : 'check-circle'"
            /></span>
            <h2>
              {{
                completed
                  ? 'Completed inspection'
                  : issues.length
                  ? 'A few things to finish'
                  : 'Ready to complete'
              }}
            </h2>
            <p class="muted">
              {{
                completed
                  ? 'Your inspection is protected and retained in history.'
                  : 'Review the vehicle, evidence and findings before completing.'
              }}
            </p>
            <dl class="detail-grid">
              <div>
                <dt>Vehicle</dt>
                <dd>{{ job.service_item_name }}</dd>
              </div>
              <div>
                <dt>Job Card</dt>
                <dd>{{ job.name }}</dd>
              </div>
              <div>
                <dt>Stage</dt>
                <dd>{{ stageLabel }}</dd>
              </div>
              <div>
                <dt>Reference</dt>
                <dd>{{ inspection.name }}</dd>
              </div>
            </dl>
          </div>
          <div v-if="issues.length && !completed" class="panel outstanding">
            <h3>Outstanding requirements</h3>
            <button
              v-for="issue in issues"
              :key="issue.label"
              @click="move(issue.step)"
            >
              <FieldIcon name="alert-circle" /><span>{{ issue.label }}</span
              ><FieldIcon name="chevron-right" />
            </button>
          </div>
          <div class="panel review-checks">
            <button @click="move(1)">
              <FieldIcon name="check-square" /><span
                >Checklist<small
                  >{{ answered }} of {{ checklist.length }} answered</small
                ></span
              ><FieldIcon name="chevron-right" /></button
            ><button @click="move(2)">
              <FieldIcon name="camera" /><span
                >Photo evidence<small
                  >{{ photos.length }} photographs ·
                  {{ requiredPhotos.filter((row) => row.photograph).length }} /
                  {{ requiredPhotos.length }} required item photos</small
                ></span
              ><FieldIcon name="chevron-right" /></button
            ><button @click="move(3)">
              <FieldIcon name="map-pin" /><span
                >GPS location<small>{{
                  values.gps_captured_at
                    ? 'Captured · ' + values.gps_accuracy + ' m accuracy'
                    : inspection.require_gps_snapshot
                    ? 'Required — not captured'
                    : 'Optional — not captured'
                }}</small></span
              ><FieldIcon name="chevron-right" />
            </button>
            <div class="review-findings">
              <h3>Findings</h3>
              <p>
                {{
                  values.inspection_remarks ||
                  'No additional findings recorded.'
                }}
              </p>
              <small v-if="values.mileage">Mileage: {{ values.mileage }}</small>
            </div>
          </div>
          <div v-if="completed" class="panel completion-metadata">
            <p>
              <strong>Completed by</strong> {{ inspection.completed_by || '—' }}
            </p>
            <p>
              <strong>Completed at</strong>
              {{ formatCaptureTime(inspection.inspected_on) }}
            </p>
            <button
              class="button secondary"
              :disabled="locked || !online"
              @click="$emit('correction')"
            >
              <FieldIcon name="edit-3" />Create correction</button
            ><slot name="correction"></slot>
          </div>
        </section>
      </div>
    </div>
    <div class="wizard-actions">
      <p
        v-if="statusMessage || !online || uploading"
        class="save-message"
        role="status"
      >
        {{
          uploading
            ? 'Uploading private photo: ' + uploadProgress + '%'
            : !online
            ? 'Offline — reconnect to save.'
            : statusMessage
        }}
      </p>
      <div class="wizard-buttons">
        <button
          class="button secondary"
          :disabled="step === 0"
          @click="move(step - 1)"
        >
          <FieldIcon name="arrow-left" /><span>Back</span></button
        ><button
          v-if="!completed"
          class="button secondary save-draft"
          :disabled="locked || !online"
          @click="$emit('save')"
        >
          <FieldIcon name="save" /><span>Save Draft</span></button
        ><button
          v-if="step < 4"
          class="button primary next-step"
          @click="move(step + 1)"
        >
          Next<FieldIcon name="arrow-right" /></button
        ><button
          v-else-if="!completed"
          class="button primary complete-inspection"
          :disabled="locked || !online || issues.length > 0"
          @click="$emit('complete')"
        >
          <FieldIcon name="check" />Complete Inspection</button
        ><button
          v-else
          class="button primary"
          :disabled="locked"
          @click="$emit('back')"
        >
          Job Card<FieldIcon name="arrow-right" />
        </button>
      </div>
    </div>
    <dialog
      ref="photoDialog"
      class="photo-dialog"
      aria-label="Review inspection photograph"
      @close="previewIndex = null"
    >
      <template v-if="selectedPhoto"
        ><div class="photo-dialog-heading">
          <strong>Photo {{ previewIndex + 1 }} of {{ photos.length }}</strong
          ><button
            class="icon-button"
            aria-label="Close photo review"
            @click="photoDialog.close()"
          >
            <FieldIcon name="x" />
          </button>
        </div>
        <img :src="selectedPhoto.file_url" :alt="selectedPhoto.file_name" />
        <p>{{ selectedPhoto.file_name }}</p>
        <div class="photo-dialog-actions">
          <button
            class="button secondary"
            :disabled="previewIndex === 0"
            @click="previewIndex--"
          >
            Previous</button
          ><a
            class="button secondary"
            :href="selectedPhoto.file_url"
            target="_blank"
            rel="noopener"
            >Open original</a
          ><button
            class="button secondary"
            :disabled="previewIndex + 1 === photos.length"
            @click="previewIndex++"
          >
            Next
          </button>
        </div></template
      >
    </dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import FieldIcon from './FieldIcon.vue'
import {
  formatCaptureTime,
  answerChoices,
  inspectionIssues,
  inspectionSteps as steps,
} from './inspectionUi'
const props = defineProps({
  inspection: Object,
  checklist: Array,
  values: Object,
  photos: Array,
  job: Object,
  online: Boolean,
  busy: Boolean,
  uploading: Boolean,
  uploadProgress: Number,
  gpsBusy: Boolean,
  gpsMessage: String,
  statusMessage: String,
  failedUpload: String,
})
defineEmits([
  'back',
  'save',
  'complete',
  'upload',
  'retry',
  'gps',
  'correction',
])
const completed = computed(
  () => props.inspection.inspection_status === 'Completed'
)
const step = ref(completed.value ? 4 : 0)
const expanded = ref(
  Math.max(
    0,
    props.checklist.findIndex((row) => !row.answer)
  )
)
const locked = computed(() => props.busy || props.uploading || props.gpsBusy)
const titles = [
  'Vehicle details',
  'Every detail matters',
  'Capture the evidence',
  'Record your findings',
  'Review your inspection',
]
const stageLabel = computed(() =>
  props.inspection.inspection_stage === 'Pre-Service'
    ? 'Pre-Inspection'
    : 'Post-Inspection'
)
const answered = computed(
  () => props.checklist.filter((row) => String(row.answer || '').trim()).length
)
const requiredPhotos = computed(() =>
  props.checklist.filter((row) => row.require_photo)
)
const issues = computed(() =>
  inspectionIssues(
    props.inspection,
    props.checklist,
    props.values,
    props.photos
  )
)
const previewIndex = ref(null),
  photoDialog = ref(null)
const selectedPhoto = computed(() =>
  previewIndex.value == null ? null : props.photos[previewIndex.value]
)
function move(index) {
  step.value = Math.max(0, Math.min(4, index))
  window.scrollTo({ top: 0, behavior: 'instant' })
}
async function openPhoto(index) {
  previewIndex.value = index
  await nextTick()
  photoDialog.value.showModal()
}
</script>
