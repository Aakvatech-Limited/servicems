<template>
  <div class="flex">
    <Sidebar />
    <div class="flex-1 max-w-5xl py-9 mx-auto">
      <h1 class="text-3xl font-bold text-center">Welcome to Booking Page</h1>
      <br><br>
      <DateFilter />
      <br><br>
      <div>
        <BookingList />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Dialog } from 'frappe-ui'
import { createResource } from 'frappe-ui'
import { session } from '../data/session'
import Sidebar from '@/components/Sidebar.vue'
import DateFilter from '@/components/DateFilter.vue'
import BookingList from '@/components/BookingList.vue'

const ping = createResource({
  url: 'ping',
  auto: true,
})

const showDialog = ref(false)
</script>
