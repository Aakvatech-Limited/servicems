<template>
  <div class="flex">
    <Sidebar />
    <div class="flex-1 max-w-7xl py-8 mx-auto w-full">
      <h1 class="text-3xl font-bold text-center">Welcome to Booking Page</h1>
      <BookingList />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { session } from '../data/session'
import Sidebar from '@/components/Sidebar.vue'
import BookingList from '@/components/BookingList.vue'

const ping = createResource({
  url: 'ping',
  auto: true,
})

</script>
