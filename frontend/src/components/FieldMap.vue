<template>
    <div class="flex flex-col gap-6">
      <div
        v-for="section in sections"
        :key="section.label"
        class="first:border-t-0 first:pt-0"
        :class="section.hideBorder ? '' : 'border-t pt-4'"
      >
        <div
          v-if="!section.hideLabel && section.doctype == 'Service Booking'"
          class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-cyan-700 font-mono leading-5"
        >
          {{ section.label }}
        </div>
        <div
          class="grid gap-6"
          :class="
            section.columns
              ? 'grid-cols-' + section.columns
              : 'grid-cols-4 sm:grid-cols-4'
          "
          v-if="section.doctype == 'Service Booking'"
        >
          <Fields :section="section" :data="data" />
        </div>
        <div
          v-if="!section.hideLabel && section.doctype == 'Customer' && data['Service Booking']['is_new_customer']"
          class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-cyan-700 font-mono leading-5"
        >
          {{ section.label }}
        </div>
        <div
          class="grid gap-4"
          :class="
            section.columns
              ? 'grid-cols-' + section.columns
              : 'grid-cols-3 sm:grid-cols-3'
          "
          v-if="section.doctype == 'Customer' && data['Service Booking']['is_new_customer']"
        >
          <Fields :section="section" :data="data" />
        </div>
        <div
          v-if="!section.hideLabel && section.doctype == 'Service Vehicle' && data['Service Booking']['is_new_vehicle']"
          class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-cyan-700 font-mono leading-5"
        >
          {{ section.label }}
        </div>
        <div
          class="grid gap-4"
          :class="
            section.columns
              ? 'grid-cols-' + section.columns
              : 'grid-cols-3 sm:grid-cols-3'
          "
          v-if="section.doctype == 'Service Vehicle' && data['Service Booking']['is_new_vehicle']"
        >
          <Fields :section="section" :data="data" />
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import Fields from '../components/Fields.vue';
  
  const props = defineProps({
    sections: Array,
    data: Object,
  })
  
  </script>
  
  <style scoped>
  :deep(.form-control.prefix select) {
    padding-left: 2rem;
  }
  </style>
  