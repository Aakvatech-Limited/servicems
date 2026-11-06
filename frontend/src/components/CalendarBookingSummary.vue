<template>
  <span class="sm-booking-summary" :class="{ 'sm-compact': compact }">
    <span class="sm-booking-heading">
      <strong>{{ booking.name }}</strong>
      <span class="sm-booking-time">{{ timeLabel(booking.booking_time) }}</span>
    </span>
    <span class="sm-booking-vehicle">{{ booking.registration_number }}</span>
    <span v-if="booking.vehicle_model" class="sm-booking-model">
      {{ booking.vehicle_model
      }}<template v-if="showBay && booking.bay"> · {{ booking.bay }}</template>
    </span>
    <span class="sm-booking-customer">{{ booking.customer_name }}</span>
    <span class="sm-status" :class="statusClass">{{ booking.status }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { timeLabel } from '@/utils/calendarViews.mjs'
const props = defineProps({
  booking: { type: Object, required: true },
  compact: Boolean,
  showBay: Boolean,
})
const statusClass = computed(
  () =>
    ({
      Pending: 'sm-status-pending',
      'In Progress': 'sm-status-progress',
      Completed: 'sm-status-complete',
      Closed: 'sm-status-closed',
    }[props.booking.status])
)
</script>

<style scoped>
.sm-booking-summary {
  display: grid;
  gap: 4px;
  min-width: 0;
  font-size: 12px;
}
.sm-booking-heading {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 8px;
}
.sm-booking-heading strong {
  overflow-wrap: anywhere;
}
.sm-booking-time {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.sm-booking-vehicle {
  font-weight: 600;
}
.sm-booking-model,
.sm-booking-customer {
  color: #586478;
  overflow-wrap: anywhere;
}
.sm-status {
  justify-self: start;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 600;
}
.sm-status-pending {
  background: #f3e8ff;
  color: #6b21a8;
}
.sm-status-progress {
  background: #fff0c2;
  color: #92400e;
}
.sm-status-complete {
  background: #dcfce7;
  color: #166534;
}
.sm-status-closed {
  background: #e5e7eb;
  color: #374151;
}
.sm-compact {
  font-size: 11px;
  gap: 2px;
}
.sm-compact .sm-booking-heading {
  display: grid;
}
.sm-compact .sm-booking-customer {
  display: none;
}
</style>
