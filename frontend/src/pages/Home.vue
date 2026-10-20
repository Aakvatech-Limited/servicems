<template>
  <div class="flex flex-col md:flex-row">
    <Sidebar />
    <div class="flex-1 min-w-0 max-w-7xl py-8 px-4 mx-auto w-full">
      <h1 class="text-3xl font-bold text-center">Welcome to Booking Page</h1>
      <BookingList />
    </div>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import BookingList from '@/components/BookingList.vue'
</script>
