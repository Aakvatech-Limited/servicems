<template>
  <div class="h-screen w-60 bg-blue-400 flex flex-col items-start p-6">
    <Button 
      class="mb-8 w-full hover:bg-cyan-500 text-black font-bold py-6 px-4 rounded"
      label="Bookings"
      @click="goToBookings()"
    />

    <Button 
      class="w-full hover:bg-green-500/50 text-black font-bold py-6 px-4 rounded"
      label="Job Card"
      @click="goToJobCard()"
    />
  </div>
</template>

<script setup>
function goToBookings() {
  window.location.href = '/app/service-booking'
}

function goToJobCard() {
  window.location.href = '/app/service-job-card'
}
</script>