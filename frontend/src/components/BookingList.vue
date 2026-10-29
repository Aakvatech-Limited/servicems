<template>
  <BookingFilter v-model="filters" />
  <p v-if="rangeError" role="alert" class="my-4 text-red-700">
    {{ rangeError }}
  </p>
  <p v-else-if="loading" role="status" class="my-4 text-gray-600">
    Loading bookings...
  </p>
  <div v-else-if="error" role="alert" class="my-4 text-red-700">
    {{ error }}
    <Button label="Retry" @click="loadBookings" />
  </div>
  <section v-else aria-label="Booking calendar" class="mt-6">
    <p class="mb-3 text-sm text-gray-600">{{ range.from }} — {{ range.to }}</p>
    <div class="calendar-grid mb-2" aria-hidden="true">
      <span
        v-for="day in weekdays"
        :key="day"
        class="text-center font-semibold text-gray-600"
        >{{ day }}</span
      >
    </div>
    <div class="calendar-grid">
      <div
        v-for="n in leadingDays"
        :key="`empty-${n}`"
        class="calendar-placeholder"
      />
      <article
        v-for="day in days"
        :key="day.date"
        :data-date="day.date"
        class="flex min-h-[180px] min-w-0 flex-col rounded-lg border border-gray-200 bg-white p-3"
        :class="{ 'ring-2 ring-cyan-600': day.date === today }"
      >
        <header class="mb-3 flex flex-wrap items-center justify-between gap-1">
          <h2 class="font-semibold">
            <time :datetime="day.date">{{ day.label }}</time>
          </h2>
          <span class="text-sm text-gray-500">{{ day.bookings.length }}</span>
        </header>
        <div class="flex flex-1 flex-col gap-2">
          <a
            v-for="booking in day.bookings"
            :key="booking.name"
            :href="`/app/service-booking/${encodeURIComponent(booking.name)}`"
            class="rounded border border-cyan-100 bg-cyan-50 p-2 text-sm text-gray-900 hover:bg-cyan-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-700"
          >
            <span class="block break-words font-semibold">{{
              booking.customer_name
            }}</span>
          </a>
          <p v-if="!day.bookings.length" class="text-sm text-gray-500">
            No bookings
          </p>
        </div>
        <button
          class="mt-3 min-h-[36px] rounded bg-gray-100 px-2 text-sm font-semibold hover:bg-gray-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-700"
          :aria-label="`Add booking for ${day.date}`"
          @click="addBooking(day.date)"
        >
          + Add
        </button>
      </article>
    </div>
  </section>
  <CreateBooking
    v-if="showDialog"
    :show-dialog="showDialog"
    :booking-date="bookingDate"
    :workshop="filters.workshop"
    :vehicle="filters.vehicle"
    @closeDialog="showDialog = false"
    @refreshData="loadBookings"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { format, parseISO } from 'date-fns'
import CreateBooking from './CreateBooking.vue'
import BookingFilter from './BookingFilter.vue'
import { calendarDays, dateRange } from '@/utils/bookingCalendar.mjs'

const today = format(new Date(), 'yyyy-MM-dd')
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const filters = ref({
  from_date: today,
  to_date: '',
  workshop: '',
  vehicle: '',
})
const records = ref([])
const loading = ref(false)
const error = ref('')
const showDialog = ref(false)
const bookingDate = ref('')
const range = computed(() =>
  dateRange(filters.value.from_date || today, filters.value.to_date),
)
const rangeError = computed(() => range.value.error)
const days = computed(() =>
  rangeError.value ? [] : calendarDays(range.value, records.value),
)
const leadingDays = computed(() =>
  days.value.length ? (parseISO(days.value[0].date).getDay() + 6) % 7 : 0,
)
let requestId = 0

async function loadBookings() {
  const currentRequest = ++requestId
  error.value = ''
  records.value = []
  if (rangeError.value) {
    loading.value = false
    return
  }
  loading.value = true
  try {
    const data = await frappeRequest({
      url: 'servicems.api.bookings.get_calendar_bookings',
      method: 'GET',
      params: {
        ...filters.value,
        from_date: range.value.from,
        to_date: range.value.to,
      },
    })
    if (currentRequest === requestId) records.value = data
  } catch (err) {
    if (currentRequest === requestId)
      error.value = err.messages?.join('\n') || err.message
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

function addBooking(date) {
  bookingDate.value = date
  showDialog.value = true
}

watch(filters, loadBookings, { deep: true, immediate: true })
</script>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.5rem;
}
@media (max-width: 1100px) {
  .calendar-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .calendar-grid[aria-hidden],
  .calendar-placeholder {
    display: none;
  }
}
@media (max-width: 600px) {
  .calendar-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
