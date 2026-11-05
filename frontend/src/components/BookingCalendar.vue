<template>
  <section
    class="sm-calendar w-full p-3 sm:p-4"
    :class="{ 'sm-dialog-open': selected || showCreate }"
    aria-label="Booking Calendar"
  >
    <header class="sm-calendar-intro mb-3 flex items-center justify-between gap-3">
      <p class="sm-calendar-subtitle text-xs">
        Workshop booking schedule · Start times in {{ timezone }}
      </p>
      <button
        v-if="canCreate"
        class="sm-primary"
        type="button"
        @click="openCreate()"
      >
        + New Booking
      </button>
    </header>

    <div
      class="sm-calendar-toolbar mb-3 flex flex-wrap items-center justify-between gap-3"
    >
      <div class="flex items-center gap-2">
        <button
          class="sm-control"
          type="button"
          aria-label="Previous period"
          @click="step(-1)"
        >
          ‹
        </button>
        <button class="sm-control" type="button" @click="goToday">Today</button>
        <button
          class="sm-control"
          type="button"
          aria-label="Next period"
          @click="step(1)"
        >
          ›
        </button>
        <strong class="ml-1 text-sm">{{ rangeLabel }}</strong>
      </div>
      <div
        class="sm-view-switch flex rounded-md border border-gray-200 p-1"
        role="group"
        aria-label="Calendar view"
      >
        <button
          v-for="option in ['day', 'week', 'month']"
          :key="option"
          type="button"
          class="rounded px-3 py-2 text-sm capitalize"
          :class="
            view === option
              ? 'bg-blue-100 font-semibold text-blue-800'
              : 'text-gray-600'
          "
          :aria-pressed="view === option"
          @click="setView(option)"
        >
          {{ option }}
        </button>
      </div>
    </div>

    <div class="sm-filter-bar mb-3">
      <label class="sm-field">
        <span>Workshop</span>
        <select v-model="workshop" class="sm-input">
          <option value="">All workshops</option>
          <option v-for="name in workshops" :key="name" :value="name">
            {{ name }}
          </option>
        </select>
      </label>
      <label class="sm-field sm-filter-search">
        <span>Search bookings</span>
        <input
          v-model="query"
          class="sm-input"
          type="search"
          maxlength="100"
          placeholder="Customer, registration or booking ID"
        />
      </label>
      <label class="sm-field sm-filter-status">
        <span>Status</span>
        <select v-model="status" class="sm-input">
          <option value="">All statuses</option>
          <option v-for="name in statuses" :key="name" :value="name">
            {{ name }}
          </option>
        </select>
      </label>
      <button
        type="button"
        class="sm-control sm-filter-toggle"
        :aria-expanded="showFilters"
        aria-controls="sm-advanced-calendar-filters"
        @click="showFilters = !showFilters"
      >
        {{ showFilters ? 'Less filters' : 'More filters' }}{{ advancedFilterCount ? ' (' + advancedFilterCount + ')' : '' }}
      </button>
    </div>
    <div
      v-if="showFilters"
      id="sm-advanced-calendar-filters"
      class="sm-advanced-filters mb-4"
    >
      <label class="sm-field">
        <span>Customer</span>
        <RecordLink
          v-model="customer"
          doctype="Customer"
          label="Filter Customer"
          placeholder="All customers"
        />
      </label>
      <label class="sm-field">
        <span>Vehicle</span>
        <RecordLink
          v-model="vehicle"
          doctype="Service Vehicle"
          label="Filter Vehicle"
          placeholder="All vehicles"
          :filters="customer ? { customer } : {}"
        />
      </label>
      <button v-if="activeFilters" type="button" class="sm-control sm-filter-clear" @click="clearFilters">
        Clear all filters
      </button>
    </div>

    <div v-if="loading" role="status" class="sm-message">Loading bookings…</div>
    <div v-else-if="error" role="alert" class="sm-message text-red-700">
      {{ error }}
      <button class="sm-control ml-3" type="button" @click="load">Retry</button>
    </div>
    <template v-else>
      <div v-if="view === 'month'" class="sm-month-legend hidden lg:flex" aria-label="Booking status legend">
        <span v-for="item in statuses" :key="item" class="sm-legend-item">
          <span class="sm-legend-dot" :class="statusClass(item)" aria-hidden="true"></span>
          {{ item }}
        </span>
      </div>
      <div v-if="view === 'month'" class="sm-month-layout hidden lg:block">
        <div class="sm-month-weekdays grid grid-cols-7 gap-1 text-center text-xs font-bold">
          <span v-for="label in weekdays" :key="label" class="p-2">{{ label }}</span>
        </div>
        <div class="sm-month-grid grid grid-cols-7 gap-1" role="grid" aria-label="Monthly bookings">
          <div
            v-for="(day, idx) in monthCells"
            :key="idx"
            class="sm-month-cell"
            :class="{
              'sm-month-outside': !day,
              'sm-month-today': day && day === localToday(),
              'sm-month-selected': day && day === agendaDate,
            }"
          >
            <template v-if="day">
              <div class="sm-month-cell-header">
                <button
                  type="button"
                  class="sm-month-day-number"
                  :aria-label="'Open day ' + day"
                  @click="focusDay(day)"
                >
                  {{ Number(day.slice(-2)) }}
                </button>
                <span v-if="recordsForDay(day).length" class="sm-month-count">
                  {{ recordsForDay(day).length }}
                </span>
              </div>
              <div class="sm-month-events">
                <button
                  v-for="booking in recordsForDay(day).slice(0, 3)"
                  :key="booking.name"
                  type="button"
                  class="sm-month-booking"
                  :class="statusClass(booking.status)"
                  :title="booking.name + ' · ' + booking.status + ' · ' + booking.customer_name"
                  :aria-label="booking.name + ', ' + timeLabel(booking.booking_time) + ', ' + booking.registration_number + ', ' + booking.status"
                  @click="selectBooking(booking)"
                >
                  <span class="sm-month-time">{{ timeLabel(booking.booking_time) }}</span>
                  <span class="sm-month-registration">{{ booking.registration_number }}</span>
                </button>
                <button
                  v-if="recordsForDay(day).length > 3"
                  class="sm-month-more"
                  type="button"
                  :aria-label="'Show all ' + recordsForDay(day).length + ' bookings on ' + day"
                  @click="focusDay(day)"
                >
                  +{{ recordsForDay(day).length - 3 }} more
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div v-else-if="view === 'week'" class="hidden lg:flex gap-3">
        <div class="min-w-0 flex-1">
          <div
            class="grid gap-px overflow-hidden rounded-lg border border-gray-200 bg-gray-200"
            :style="{ gridTemplateColumns: '165px repeat(7, minmax(0, 1fr))' }"
          >
            <div class="bg-gray-50 p-3 text-xs font-bold">
              {{ bayManagementEnabled ? 'Workshop / Bay' : 'Workshop' }}
            </div>
            <div
              v-for="day in visibleDays"
              :key="day"
              class="sm-week-heading bg-gray-50 text-center text-xs font-semibold"
              :class="{ 'sm-selected-day': day === agendaDate }"
            >
              <button
                type="button"
                class="w-full p-3"
                :aria-pressed="day === agendaDate"
                @click="agendaDate = day"
              >
                {{ formatDay(day, { weekday: 'short' }) }}
                <span class="block font-normal">{{
                  formatDay(day, { day: 'numeric', month: 'short' })
                }}</span>
              </button>
            </div>
            <template v-for="group in groups" :key="group.key">
              <div class="bg-white p-3 text-sm font-semibold">
                {{ group.label }}
                <div
                  v-if="group.workshop"
                  class="mt-1 text-xs font-normal text-gray-500"
                >
                  {{ group.workshop }}
                </div>
              </div>
              <div
                v-for="day in visibleDays"
                :key="group.key + day"
                class="min-h-[100px] bg-white p-1"
              >
                <button
                  v-for="booking in group.entries.filter(
                    (item) => item.booking_date === day
                  )"
                  :key="booking.name"
                  type="button"
                  class="sm-event mb-1 w-full text-left"
                  :class="statusClass(booking.status)"
                  @click="selectBooking(booking)"
                >
                  <BookingSummary :booking="booking" compact />
                </button>
              </div>
            </template>
          </div>
        </div>
        <aside
          class="hidden xl:block w-60 shrink-0 rounded-lg border border-gray-200 bg-gray-50 p-3"
        >
          <h2 class="text-sm font-bold">
            {{
              formatDay(agendaDate, {
                weekday: 'short',
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })
            }}
          </h2>
          <p class="my-2 text-xs text-gray-500">
            {{ recordsForDay(agendaDate).length }} bookings
          </p>
          <div class="mb-3 flex gap-2">
            <button
              type="button"
              class="sm-control"
              @click="agendaDate = addDays(agendaDate, -1)"
            >
              ‹
            </button>
            <button
              type="button"
              class="sm-control"
              @click="agendaDate = addDays(agendaDate, 1)"
            >
              ›
            </button>
          </div>
          <button
            v-for="booking in recordsForDay(agendaDate)"
            :key="booking.name"
            class="sm-agenda mb-2 w-full text-left"
            :class="statusClass(booking.status)"
            type="button"
            @click="selectBooking(booking)"
          >
            <BookingSummary
              :booking="booking"
              :show-bay="bayManagementEnabled"
            />
          </button>
          <p
            v-if="!recordsForDay(agendaDate).length"
            class="text-xs text-gray-500"
          >
            No bookings on this date.
          </p>
        </aside>
      </div>

      <div v-else-if="view === 'day'" class="hidden md:block">
        <div class="flex gap-4">
          <div
            class="min-w-0 flex-1 rounded-lg border border-gray-200 bg-white p-4"
          >
            <h2 class="mb-3 text-base font-semibold">
              {{
                formatDay(cursor, {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })
              }}
            </h2>
            <p
              v-if="!recordsForDay(cursor).length"
              class="text-sm text-gray-500"
            >
              No bookings on this day.
            </p>
            <button
              v-for="booking in recordsForDay(cursor)"
              :key="booking.name"
              type="button"
              class="sm-agenda mb-2 w-full text-left"
              :class="statusClass(booking.status)"
              @click="selectBooking(booking)"
            >
              <BookingSummary
                :booking="booking"
                :show-bay="bayManagementEnabled"
              />
            </button>
          </div>
          <aside
            class="hidden xl:block w-64 shrink-0 rounded-lg border border-gray-200 bg-gray-50 p-4"
          >
            <h3 class="font-bold">Day summary</h3>
            <p class="mt-1 text-sm text-gray-500">
              {{ recordsForDay(cursor).length }} bookings
            </p>
            <p class="mt-4 text-xs text-gray-500">
              Select a booking to view or edit it.
            </p>
          </aside>
        </div>
      </div>

      <div
        class="lg:hidden"
        :class="view === 'day' ? 'md:hidden' : ''"
      >
        <h2 class="mb-3 text-base font-semibold">
          {{
            formatDay(agendaDate, {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })
          }}
        </h2>
        <label class="mb-3 block text-sm"
          >Agenda date
          <input v-model="agendaDate" type="date" class="sm-input mt-1" />
        </label>
        <div v-if="!recordsForDay(agendaDate).length" class="sm-message">
          No bookings for this date.
        </div>
        <button
          v-for="booking in recordsForDay(agendaDate)"
          :key="booking.name"
          type="button"
          class="sm-agenda mb-2 w-full text-left"
          :class="statusClass(booking.status)"
          @click="selectBooking(booking)"
        >
          <BookingSummary :booking="booking" :show-bay="bayManagementEnabled" />
        </button>
      </div>
      <p v-if="!bookings.length" class="mt-4 text-sm text-gray-500">
        No bookings match these filters.
      </p>
    </template>

    <div v-if="selected" class="sm-details-modal" @click.self="selected = null">
      <section
        class="sm-details-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Booking details"
      >
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-lg font-bold">
              {{ selected.registration_number }}
            </h2>
            <p class="text-sm text-gray-600">{{ selected.customer_name }}</p>
          </div>
          <button
            type="button"
            class="sm-control"
            aria-label="Close booking details"
            @click="selected = null"
          >
            ✕
          </button>
        </div>
        <dl class="my-4 grid grid-cols-2 gap-2 text-sm">
          <dt>Date</dt>
          <dd>{{ selected.booking_date }}</dd>
          <dt>Time</dt>
          <dd>{{ timeLabel(selected.booking_time) }}</dd>
          <dt>Workshop</dt>
          <dd>{{ selected.workshop }}</dd>
          <dt>Status</dt>
          <dd>{{ selected.status }}</dd>
          <template v-if="bayManagementEnabled && selected.bay"
            ><dt>Bay</dt>
            <dd>{{ selected.bay }}</dd></template
          >
        </dl>
        <div class="flex flex-wrap gap-2">
          <a class="sm-control" :href="bookingUrl(selected)" target="_top"
            >Open Booking</a
          >
          <a
            v-if="selected.job_card"
            class="sm-control"
            :href="jobCardUrl(selected)"
            target="_top"
            >Open Job Card</a
          >
          <button
            v-if="canWrite && selected.status === 'Pending'"
            type="button"
            class="sm-primary"
            @click="rescheduleOpen = true"
          >
            Reschedule
          </button>
        </div>
        <form
          v-if="rescheduleOpen && selected.status === 'Pending'"
          class="mt-4 grid gap-2"
          @submit.prevent="reschedule"
        >
          <label class="sm-field"
            ><span>New Date</span
            ><input
              v-model="rescheduleDate"
              type="date"
              required
              class="sm-input"
          /></label>
          <label class="sm-field"
            ><span>Start Time</span
            ><input v-model="rescheduleTime" type="time" class="sm-input"
          /></label>
          <label v-if="bayManagementEnabled" class="sm-field"
            ><span>Bay</span>
            <select v-model="rescheduleBay" class="sm-input">
              <option value="">No Bay</option>
              <option
                v-for="bay in bays.filter(
                  (b) => b.service_workshop === selected.workshop
                )"
                :key="bay.name"
                :value="bay.name"
              >
                {{ bay.name }}
              </option>
            </select>
          </label>
          <div v-if="mutationError" role="alert" class="text-sm text-red-700">
            {{ mutationError }}
          </div>
          <button type="submit" class="sm-primary" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save Reschedule' }}
          </button>
        </form>
      </section>
    </div>

    <CreateBooking
      :show-dialog="showCreate"
      :booking_date="bookingDate"
      :workshop="workshop"
      @closeDialog="showCreate = false"
      @refreshData="load"
    />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import CreateBooking from './CalendarCreateBooking.vue'
import RecordLink from './CalendarRecordLink.vue'
import BookingSummary from './CalendarBookingSummary.vue'
import {
  addDays,
  daysBetween,
  formatDay,
  monthStart,
  rowGroups,
  rescheduleTimeValue,
  shiftDate,
  timeLabel,
  viewRange,
  siteToday,
} from '@/utils/calendarViews.mjs'

const statuses = ['Pending', 'In Progress', 'Completed', 'Closed']
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const timezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone)
const localToday = () => siteToday(timezone.value)
const cursor = ref(localToday())
const agendaDate = ref(cursor.value)
const view = ref('week')
const workshop = ref('')
const status = ref('')
const customer = ref('')
const vehicle = ref('')
const showFilters = ref(false)
const advancedFilterCount = computed(
  () => [customer.value, vehicle.value].filter(Boolean).length
)
const activeFilters = computed(
  () =>
    [
      workshop.value,
      customer.value,
      vehicle.value,
      status.value,
      query.value,
    ].filter(Boolean).length
)
function clearFilters() {
  workshop.value = ''
  customer.value = ''
  vehicle.value = ''
  status.value = ''
  query.value = ''
}
const canCreate = ref(false)
const canWrite = ref(false)
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
const visibleDays = computed(() =>
  daysBetween(range.value.from, range.value.to)
)
const rangeLabel = computed(() =>
  view.value === 'day'
    ? formatDay(cursor.value, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : view.value === 'month'
    ? formatDay(cursor.value, { month: 'long', year: 'numeric' })
    : formatDay(range.value.from, { day: 'numeric', month: 'short' }) +
      ' – ' +
      formatDay(range.value.to, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
)
const monthCells = computed(() => {
  const first = monthStart(cursor.value)
  const leading = (new Date(first + 'T00:00:00Z').getUTCDay() + 6) % 7
  const days = [...Array(leading).fill(null), ...visibleDays.value]
  const trailing = (7 - (days.length % 7)) % 7
  return [...days, ...Array(trailing).fill(null)]
})
const groups = computed(() =>
  rowGroups(
    bookings.value,
    bayManagementEnabled.value,
    bays.value,
    workshop.value
  )
)
let initialized = false
let requestNumber = 0
let searchTimer
function recordsForDay(day) {
  return bookings.value.filter((item) => item.booking_date === day)
}
function statusClass(status) {
  return status === 'Completed'
    ? 'sm-complete'
    : status === 'In Progress'
    ? 'sm-progress'
    : status === 'Closed'
    ? 'sm-closed'
    : 'sm-pending'
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
  rescheduleTime.value =
    timeLabel(item.booking_time) === 'Time not set'
      ? ''
      : timeLabel(item.booking_time)
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
      frappeRequest({
        url: 'servicems.api.calendar.get_calendar_bookings',
        method: 'GET',
        params: {
          from_date: range.value.from,
          to_date: range.value.to,
          workshop: workshop.value,
          status: status.value,
          customer: customer.value,
          vehicle: vehicle.value,
          search: query.value,
        },
      }),
      frappeRequest({
        url: 'frappe.client.get_list',
        method: 'GET',
        params: {
          doctype: 'Service Workshop',
          fields: JSON.stringify(['name']),
          limit_page_length: 500,
        },
      }),
    ])
    if (id !== requestNumber) return
    timezone.value = response.timezone || timezone.value
    canCreate.value = Boolean(response.can_create)
    canWrite.value = Boolean(response.can_write)
    if (!initialized) {
      initialized = true
      const today = localToday()
      if (cursor.value !== today) {
        cursor.value = today
        agendaDate.value = today
        return
      }
    }
    bookings.value = response.bookings || []
    bays.value = response.bays || []
    bayManagementEnabled.value = Boolean(response.bay_management_enabled)
    workshops.value = (lookup || []).map((item) => item.name)
  } catch (e) {
    if (id === requestNumber)
      error.value =
        e.messages?.join(' ') || e.message || 'Unable to load bookings.'
  } finally {
    if (id === requestNumber) loading.value = false
  }
}
async function reschedule() {
  if (saving.value || !selected.value) return
  saving.value = true
  mutationError.value = ''
  try {
    await frappeRequest({
      url: 'servicems.api.calendar.reschedule_booking',
      method: 'POST',
      params: {
        name: selected.value.name,
        booking_date: rescheduleDate.value,
        booking_time: rescheduleTimeValue(
          rescheduleTime.value,
          selected.value.booking_time
        ),
        bay: bayManagementEnabled.value ? rescheduleBay.value : undefined,
      },
    })
    selected.value = null
    rescheduleOpen.value = false
    await load()
  } catch (e) {
    mutationError.value =
      e.messages?.join(' ') || e.message || 'Unable to reschedule.'
  } finally {
    saving.value = false
  }
}
watch([cursor, view, workshop, status, customer, vehicle], load, {
  immediate: true,
})
watch(customer, () => {
  vehicle.value = ''
})
watch(agendaDate, (date) => {
  if (date && (date < range.value.from || date > range.value.to))
    cursor.value = date
})
onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  requestNumber++
})
watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 300)
})
</script>

<style scoped>
.sm-calendar {
  height: 100%;
  min-width: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  color: #273244;
}
.sm-dialog-open {
  overflow: hidden;
}
.sm-details-modal {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  overflow: hidden;
  background: #0005;
}
.sm-details-dialog {
  width: 100%;
  max-width: 448px;
  max-height: 100%;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 20px;
  border-radius: 10px;
  background: white;
}
.sm-field {
  min-width: 0;
}
.sm-event {
  overflow: hidden;
  overflow-wrap: anywhere;
}
@media (max-width: 639px) {
  .sm-details-modal {
    align-items: flex-end;
    padding: 8px;
  }
}
.sm-primary {
  background: #171717;
  color: white;
  border-radius: 7px;
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
}
.sm-primary:disabled {
  opacity: 0.55;
}
.sm-control {
  border: 1px solid #dce2ec;
  border-radius: 6px;
  background: #fff;
  padding: 8px 10px;
  font-size: 13px;
}
.sm-input {
  display: block;
  width: 100%;
  border: 1px solid #dce2ec;
  background: white;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
}
.sm-field span {
  display: block;
  color: #5a687e;
  font-size: 12px;
  margin-bottom: 4px;
}
.sm-message {
  padding: 24px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  text-align: center;
}
.sm-event {
  border-left: 3px solid;
  padding: 6px;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.4;
}
.sm-pending {
  background: #faf5ff;
  border-color: #a855f7;
}
.sm-progress {
  background: #fffbeb;
  border-color: #f59e0b;
}
.sm-complete {
  background: #e8f8ee;
  border-color: #299653;
}
.sm-closed {
  background: #f8fafc;
  border-color: #64748b;
}
.sm-calendar-toolbar .sm-view-switch {
  order: -1;
}
.sm-week-heading.sm-selected-day {
  background: #eaf2ff;
  color: #1d4ed8;
}
.sm-week-heading button:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
}
.sm-agenda.sm-pending {
  border-left-color: #a855f7;
}
.sm-agenda.sm-progress {
  border-left-color: #f59e0b;
}
.sm-agenda.sm-complete {
  border-left-color: #299653;
}
.sm-agenda.sm-closed {
  border-left-color: #64748b;
}
.sm-agenda {
  border: 1px solid #e0e7f0;
  border-left: 4px solid #4b68ae;
  border-radius: 8px;
  background: white;
  padding: 12px;
}
</style>
