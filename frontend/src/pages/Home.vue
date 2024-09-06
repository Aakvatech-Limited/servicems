<template>
  <div class="flex">
    <div class="flex-1 max-w-3xl py-12 mx-auto">
      <h1 class="text-3xl font-bold text-center">Welcome to ServiceMS</h1>
      <br><br>
      <div class="flex p-2 space-x-16">
        <div class="flex-initial w-64">
          <DatePicker
            v-model="fromDate"
            variant="outline"
            placeholder="Select From Date"
            :disabled="false"
            label="From Date"
          />
        </div>
        <div class="flex-initial w-64">
          <DatePicker
            v-model="toDate"
            variant="outline"
            placeholder="Select To Date"
            :disabled="false"
            label="To Date"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Dialog } from 'frappe-ui'
import { createResource } from 'frappe-ui'
import { session } from '../data/session'

const fromDate = ref('')
const toDate = ref('')

const ping = createResource({
  url: 'ping',
  auto: true,
})

const showDialog = ref(false)
</script>
