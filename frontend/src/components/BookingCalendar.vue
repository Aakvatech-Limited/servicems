<template>
  <section class="sm-calendar mx-auto w-full max-w-[1600px] p-3 sm:p-5" aria-label="Booking Calendar">
    <header class="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Booking Calendar</h1>
        <p class="mt-1 text-sm text-gray-500">Workshop booking schedule</p>
      </div>
      <button class="sm-primary" type="button" @click="openCreate()">+ New Booking</button>
    </header>

    <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <button class="sm-control" type="button" aria-label="Previous period" @click="step(-1)">‹</button>
        <button class="sm-control" type="button" @click="goToday">Today</button>
        <button class="sm-control" type="button" aria-label="Next period" @click="step(1)">›</button>
        <strong class="ml-1 text-sm">{{ rangeLabel }}</strong>
      </div>
      <div class="flex rounded-md border border-gray-200 p-1" role="group" aria-label="Calendar view">
        <button v-for="option in ['day', 'week', 'month']" :key="option"
          type="button" class="rounded px-3 py-2 text-sm capitalize"
          :class="view === option ? 'bg-blue-100 font-semibold text-blue-800' : 'text-gray-600'"
          :aria-pressed="view === option" @click="setView(option)">{{ option }}</button>
      </div>
    </div>

    <div class="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
      <label class="sm-field"><span>Workshop</span>
        <select v-model="workshop" class="sm-input">
          <option value="">All workshops</option>
          <option v-for="name in workshops" :key="name" :value="name">{{ name }}</option>
        </select>
      </label>
      <label class="sm-field"><span>Customer / registration</span>
        <input v-model="query" class="sm-input" type="search" maxlength="100" placeholder="Search bookings" />
      </label>
      <label class="sm-field"><span>Status</span>
        <select v-model="status" class="sm-input">
          <option value="">All statuses</option>
          <option v-for="name in statuses" :key="name" :value="name">{{ name }}</option>
        </select>
      </label>
    </div>

    <div v-if="loading" role="status" class="sm-message">Loading bookings…</div>
    <div v-else-if="error" role="alert" class="sm-message text-red-700">
      {{ error }} <button class="sm-control ml-3" type="button" @click="load">Retry</button>
    </div>
    <template v-else>
      <div v-if="view === 'month'" class="hidden md:block">
        <div class="grid grid-cols-7 gap-1 text-center text-xs font-bold text-gray-500">
          <span v-for="label in weekdays" :key="label" class="p-2">{{ label }}</span>
        </div>
        <div class="grid grid-cols-7 gap-1">
          <div v-for="(day, idx) in monthCells" :key="idx" class="min-h-28 rounded-md border border-gray-200 bg-white p-2">
            <template v-if="day">
              <button class="mb-2 text-sm font-semibold" type="button" @click="focusDay(day)">{{ Number(day.slice(-2)) }}</button>
              <button v-for="booking in recordsForDay(day).slice(0, 3)" :key="booking.name"
                type="button" class="mb-1 block w-full truncate rounded bg-blue-50 px-1 py-1 text-left text-xs"
                @click="selectBooking(booking)">{{ timeLabel(booking.booking_time) }} {{ booking.registration_number }}</button>
              <button v-if="recordsForDay(day).length > 3" class="text-xs text-blue-700"
                type="button" @click="focusDay(day)">+{{ recordsForDay(day).length - 3 }} more</button>
            </template>
          </div>
        </div>
      </div>

      <div v-else-if="view === 'week'" class="hidden lg:flex gap-3">
        <div class="min-w-0 flex-1">
        <div class="grid gap-px overflow-hidden rounded-lg border border-gray-200 bg-gray-200"
          :style="{ gridTemplateColumns: '165px repeat(7, minmax(0, 1fr))' }">
          <div class="bg-gray-50 p-3 text-xs font-bold">Workshop / Bay</div>
          <div v-for="day in visibleDays" :key="day" class="bg-gray-50 p-3 text-center text-xs font-semibold">
            {{ formatDay(day, { weekday: 'short' }) }}<span class="block font-normal">{{ formatDay(day, { day: 'numeric', month: 'short' }) }}</span>
          </div>
          <template v-for="group in groups" :key="group.key">
            <div class="bg-white p-3 text-sm font-semibold">
              {{ group.label }}
              <div v-if="group.workshop" class="mt-1 text-xs font-normal text-gray-500">{{ group.workshop }}</div>
            </div>
            <div v-for="day in visibleDays" :key="group.key + day" class="min-h-[100px] bg-white p-1">
              <button v-for="booking in group.entries.filter((item) => item.booking_date === day)" :key="booking.name"
                type="button" class="sm-event mb-1 w-full text-left"
                :class="statusClass(booking.status)" @click="selectBooking(booking)">
                <span class="font-bold">{{ timeLabel(booking.booking_time) }}</span>
                <span class="block font-semibold">{{ booking.registration_number }}</span>
                <span class="block truncate">{{ booking.customer_name }}</span>
                <span class="mt-1 block text-[10px]">{{ booking.status }}</span>
              </button>
            </div>
          </template>
        </div>
        </div>
        <aside class="w-60 shrink-0 rounded-lg border border-gray-200 bg-gray-50 p-3">
          <h2 class="text-sm font-bold">{{ formatDay(agendaDate, {weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'}) }}</h2>
          <p class="my-2 text-xs text-gray-500">{{ recordsForDay(agendaDate).length }} bookings</p>
          <div class="mb-3 flex gap-2">
            <button type="button" class="sm-control" @click="agendaDate = addDays(agendaDate, -1)">‹</button>
            <button type="button" class="sm-control" @click="agendaDate = addDays(agendaDate, 1)">›</button>
          </div>
          <button v-for="booking in recordsForDay(agendaDate)" :key="booking.name"
            class="sm-agenda mb-2 w-full text-left" type="button" @click="selectBooking(booking)">
            <strong class="text-xs">{{ timeLabel(booking.booking_time) }} · {{ booking.registration_number }}</strong>
            <span class="mt-1 block text-xs">{{ booking.customer_name }}</span>
            <span class="mt-1 block text-xs text-gray-500">{{ booking.status }}</span>
          </button>
          <p v-if="!recordsForDay(agendaDate).length" class="text-xs text-gray-500">No bookings on this date.</p>
        </aside>
      </div>

      <div v-else-if="view === 'day'" class="hidden md:block">
        <div class="flex gap-4">
          <div class="min-w-0 flex-1 rounded-lg border border-gray-200 bg-white p-4">
            <h2 class="mb-3 text-base font-semibold">{{ formatDay(cursor, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}</h2>
            <p v-if="!recordsForDay(cursor).length" class="text-sm text-gray-500">No bookings on this day.</p>
            <button v-for="booking in recordsForDay(cursor)" :key="booking.name" type="button"
              class="sm-agenda mb-2 w-full text-left" @click="selectBooking(booking)">
              <strong>{{ timeLabel(booking.booking_time) }} · {{ booking.registration_number }}</strong>
              <span class="block text-sm">{{ booking.customer_name }} · {{ booking.workshop }}</span>
              <span class="text-xs">{{ booking.status }}</span>
            </button>
          </div>
          <aside class="w-64 shrink-0 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <h3 class="font-bold">Day summary</h3>
            <p class="mt-1 text-sm text-gray-500">{{ recordsForDay(cursor).length }} bookings</p>
            <p class="mt-4 text-xs text-gray-500">Select a booking to view or edit it.</p>
          </aside>
        </div>
      </div>

      <div class="lg:hidden" :class="view === 'day' || view === 'month' ? 'md:hidden' : ''">
        <h2 class="mb-3 text-base font-semibold">{{ formatDay(agendaDate, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}</h2>
        <label class="mb-3 block text-sm">Agenda date
          <input v-model="agendaDate" type="date" class="sm-input mt-1" />
        </label>
        <div v-if="!recordsForDay(agendaDate).length" class="sm-message">No bookings for this date.</div>
        <button v-for="booking in recordsForDay(agendaDate)" :key="booking.name"
          type="button" class="sm-agenda mb-2 w-full text-left" @click="selectBooking(booking)">
          <span class="flex items-center justify-between gap-3">
            <strong>{{ timeLabel(booking.booking_time) }} · {{ booking.registration_number }}</strong>
            <span class="rounded bg-gray-100 px-2 py-1 text-xs">{{ booking.status }}</span>
          </span>
          <span class="mt-1 block text-sm">{{ booking.customer_name }}</span>
          <span class="mt-1 block text-xs text-gray-500">{{ booking.workshop }}<template v-if="bayManagementEnabled && booking.bay"> · {{ booking.bay }}</template></span>
        </button>
      </div>
      <p v-if="!bookings.length" class="mt-4 text-sm text-gray-500">No bookings match these filters.</p>
    </template>

    <div v-if="selected" class="fixed inset-0 z-50 flex items-end justify-center bg-black/30 sm:items-center" @click.self="selected = null">
      <section class="w-full max-w-md rounded-t-xl bg-white p-5 shadow-lg sm:rounded-xl" role="dialog" aria-modal="true" aria-label="Booking details">
        <div class="flex items-start justify-between">
          <div><h2 class="text-lg font-bold">{{ selected.registration_number }}</h2><p class="text-sm text-gray-600">{{ selected.customer_name }}</p></div>
          <button type="button" class="sm-control" aria-label="Close booking details" @click="selected = null">✕</button>
        </div>
        <dl class="my-4 grid grid-cols-2 gap-2 text-sm">
          <dt>Date</dt><dd>{{ selected.booking_date }}</dd>
          <dt>Time</dt><dd>{{ timeLabel(selected.booking_time) }}</dd>
          <dt>Workshop</dt><dd>{{ selected.workshop }}</dd>
          <dt>Status</dt><dd>{{ selected.status }}</dd>
          <template v-if="bayManagementEnabled && selected.bay"><dt>Bay</dt><dd>{{ selected.bay }}</dd></template>
        </dl>
        <div class="flex flex-wrap gap-2">
          <a class="sm-control" :href="bookingUrl(selected)" target="_top">Open Booking</a>
          <a v-if="selected.job_card" class="sm-control" :href="jobCardUrl(selected)" target="_top">Open Job Card</a>
          <button v-if="selected.status === 'Pending'" type="button" class="sm-primary" @click="rescheduleOpen = true">Reschedule</button>
        </div>
        <form v-if="rescheduleOpen && selected.status === 'Pending'" class="mt-4 grid gap-2" @submit.prevent="reschedule">
          <label class="sm-field"><span>New Date</span><input v-model="rescheduleDate" type="date" required class="sm-input" /></label>
          <label class="sm-field"><span>Start Time</span><input v-model="rescheduleTime" type="time" class="sm-input" /></label>
          <label v-if="bayManagementEnabled" class="sm-field"><span>Bay</span>
            <select v-model="rescheduleBay" class="sm-input">
              <option value="">No Bay</option>
              <option v-for="bay in bays.filter((b) => b.service_workshop === selected.workshop)" :key="bay.name" :value="bay.name">{{ bay.name }}</option>
            </select>
          </label>
          <div v-if="mutationError" role="alert" class="text-sm text-red-700">{{ mutationError }}</div>
          <button type="submit" class="sm-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Reschedule' }}</button>
        </form>
      </section>
    </div>

    <CreateBooking :show-dialog="showCreate" :booking_date="bookingDate" :workshop="workshop"
      @closeDialog="showCreate = false" @refreshData="load" />
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import CreateBooking from './CalendarCreateBooking.vue'
import { addDays, daysBetween, formatDay, monthStart, rowGroups, shiftDate, timeLabel, viewRange, monday } from '@/utils/calendarViews.mjs'

const statuses = ['Pending', 'In Progress', 'Completed', 'Closed']
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const localToday = () => {
  const d = new Date()
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'), String(d.getDate()).padStart(2, '0')].join('-')
}
const cursor = ref(localToday())
const agendaDate = ref(cursor.value)
const view = ref('week')
const workshop = ref('')
const status = ref('')
const query = ref('')
const bookings = ref([])
const bays = ref([])
const workshops = ref([])
const bayManagementEnabled = ref(false)
const loading = ref(false)
const error = ref('')
const selected = ref(null)
const rescheduleOpen = ref(false)
const rescheduleDate = ref('')
const rescheduleTime = ref('')
const rescheduleBay = ref('')
const saving = ref(false)
const mutationError = ref('')
const showCreate = ref(false)
const bookingDate = ref('')
const range = computed(() => viewRange(cursor.value, view.value))
const visibleDays = computed(() => daysBetween(range.value.from, range.value.to))
const rangeLabel = computed(() => view.value === 'day'
  ? formatDay(cursor.value, { day: 'numeric', month: 'short', year: 'numeric' })
  : view.value === 'month'
    ? formatDay(cursor.value, { month: 'long', year: 'numeric' })
    : formatDay(range.value.from, { day: 'numeric', month: 'short' }) + ' – ' + formatDay(range.value.to, { day: 'numeric', month: 'short', year: 'numeric' }))
const monthCells = computed(() => {
  const first = monthStart(cursor.value)
  const leading = (new Date(first + 'T00:00:00Z').getUTCDay() + 6) % 7
  return [...Array(leading).fill(null), ...visibleDays.value]
})
const groups = computed(() => rowGroups(bookings.value, bayManagementEnabled.value, bays.value, workshop.value))
let requestNumber = 0
let searchTimer
function recordsForDay(day) {
  return bookings.value.filter((item) => item.booking_date === day)
}
function statusClass(status) {
  return status === 'Completed' ? 'sm-complete' : status === 'In Progress' ? 'sm-progress' : status === 'Closed' ? 'sm-closed' : 'sm-pending'
}
function setView(next) {
  view.value = next
  agendaDate.value = cursor.value
}
function focusDay(date) {
  cursor.value = date
  agendaDate.value = date
  view.value = 'day'
}
function step(direction) {
  cursor.value = shiftDate(cursor.value, view.value, direction)
  agendaDate.value = cursor.value
}
function goToday() {
  cursor.value = localToday()
  agendaDate.value = cursor.value
}
function bookingUrl(item) {
  return '/app/service-booking/' + encodeURIComponent(item.name)
}
function jobCardUrl(item) {
  return '/app/service-job-card/' + encodeURIComponent(item.job_card)
}
function selectBooking(item) {
  selected.value = item
  rescheduleDate.value = item.booking_date
  rescheduleTime.value = timeLabel(item.booking_time) === 'Time not set' ? '' : timeLabel(item.booking_time)
  rescheduleBay.value = item.bay || ''
  rescheduleOpen.value = false
  mutationError.value = ''
}
function openCreate(date = agendaDate.value) {
  bookingDate.value = date
  showCreate.value = true
}
async function load() {
  const id = ++requestNumber
  loading.value = true
  error.value = ''
  try {
    const [response, lookup] = await Promise.all([
      frappeRequest({url: 'servicems.api.calendar.get_calendar_bookings', method: 'GET',
        params: { from_date: range.value.from, to_date: range.value.to, workshop: workshop.value, status: status.value, search: query.value } }),
      frappeRequest({url: 'frappe.client.get_list', method: 'GET',
        params: {doctype: 'Service Workshop', fields: JSON.stringify(['name']), limit_page_length: 500} }),
    ])
    if (id !== requestNumber) return
    bookings.value = response.bookings || []
    bays.value = response.bays || []
    bayManagementEnabled.value = Boolean(response.bay_management_enabled)
    workshops.value = (lookup || []).map((item) => item.name)
  } catch (e) {
    if (id === requestNumber) error.value = e.messages?.join(' ') || e.message || 'Unable to load bookings.'
  } finally {
    if (id === requestNumber) loading.value = false
  }
}
async function reschedule() {
  if (saving.value || !selected.value) return
  saving.value = true
  mutationError.value = ''
  try {
    await frappeRequest({url: 'servicems.api.calendar.reschedule_booking', method: 'POST',
      params: {name: selected.value.name, booking_date: rescheduleDate.value, booking_time: rescheduleTime.value,
        bay: bayManagementEnabled.value ? rescheduleBay.value : undefined}})
    selected.value = null
    rescheduleOpen.value = false
    await load()
  } catch (e) {
    mutationError.value = e.messages?.join(' ') || e.message || 'Unable to reschedule.'
  } finally {
    saving.value = false
  }
}
watch([cursor, view, workshop, status], load, { immediate: true })
watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 300)
})
</script>

<style scoped>
.sm-calendar { color: #273244; }
.sm-primary { background: #0b5be4; color: white; border-radius: 7px; padding: 9px 14px; font-size: 13px; font-weight: 700; }
.sm-primary:disabled { opacity: .55; }
.sm-control { border: 1px solid #dce2ec; border-radius: 6px; background: #fff; padding: 8px 10px; font-size: 13px; }
.sm-input { display: block; width: 100%; border: 1px solid #dce2ec; background: white; border-radius: 6px; padding: 8px 10px; font-size: 13px; }
.sm-field span { display: block; color: #5a687e; font-size: 12px; margin-bottom: 4px; }
.sm-message { padding: 24px; border: 1px solid #e2e8f0; background: white; border-radius: 8px; text-align: center; }
.sm-event { border-left: 3px solid; padding: 6px; border-radius: 4px; font-size: 11px; line-height: 1.4; }
.sm-pending { background: #fff2da; border-color: #dc9b27; }
.sm-progress { background: #e5efff; border-color: #377cce; }
.sm-complete { background: #e8f8ee; border-color: #299653; }
.sm-closed { background: #fee6e9; border-color: #bc2230; }
.sm-agenda { border: 1px solid #e0e7f0; border-left: 4px solid #4b68ae; border-radius: 8px; background: white; padding: 12px; }
</style>
