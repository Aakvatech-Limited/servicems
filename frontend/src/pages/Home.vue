<template>
  <BookingCalendar v-if="embedded || isDevelopment" />
</template>

<script setup>
import BookingCalendar from '@/components/BookingCalendar.vue'

const isDevelopment = import.meta.env.DEV
const embedded =
  new URLSearchParams(window.location.search).get('embedded') === '1'

// The standalone website does not inherit the native Frappe Desk shell.
if (!embedded && !isDevelopment) {
  window.location.replace('/app/service-booking-calendar')
}
</script>
