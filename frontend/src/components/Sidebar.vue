<template>
  <div class="h-screen w-64 bg-gray-800 text-white flex flex-col items-start p-5">
    <Button 
      class="mb-8 w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-6 px-4 rounded"
      label="Bookings"
      @click=""
    />

    <Button 
      class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-6 px-4 rounded"
      label="Job Card"
      @click=""
    />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goToBookings() {
  router.push({ name: 'Bookings' });
}

function goToJobCard() {
  router.push({ name: 'JobCard' });
}
</script>