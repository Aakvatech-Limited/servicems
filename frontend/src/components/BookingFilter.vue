<template>
  <div
    class="mt-6 grid grid-cols-1 gap-4 rounded-xl border border-gray-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-4"
  >
    <div>
      <label for="booking-from" class="mb-2 block text-sm font-semibold"
        >From Date</label
      >
      <input
        id="booking-from"
        type="date"
        class="form-input w-full"
        :value="modelValue.from_date"
        @input="update('from_date', $event.target.value)"
      />
    </div>
    <div>
      <label for="booking-to" class="mb-2 block text-sm font-semibold"
        >To Date</label
      >
      <input
        id="booking-to"
        type="date"
        class="form-input w-full"
        :value="modelValue.to_date"
        @input="update('to_date', $event.target.value)"
      />
    </div>
    <Link
      doctype="Service Workshop"
      label="Service Workshop"
      placeholder="All workshops"
      :value="modelValue.workshop"
      @change="update('workshop', $event)"
    />
    <Link
      doctype="Service Vehicle"
      label="Service Vehicle"
      placeholder="All vehicles"
      :value="modelValue.vehicle"
      @change="update('vehicle', $event)"
    />
  </div>
</template>

<script setup>
import Link from './controls/Link.vue'

const props = defineProps({ modelValue: { type: Object, required: true } })
const emit = defineEmits(['update:modelValue'])
function update(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>
