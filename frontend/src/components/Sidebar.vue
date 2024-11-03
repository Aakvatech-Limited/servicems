<template>
  <div class="h-screen w-60 bg-blue-400 flex flex-col items-start p-6">
    <Button 
      class="mb-8 w-full bg-blue-500 hover:bg-blue-500/50 text-black font-bold py-6 px-4 rounded"
      label="Bookings"
      @click="goToBookings()"
    />

    <Button 
      class="w-full bg-green-500 hover:bg-green-500 text-black font-bold py-6 px-4 rounded"
      label="Job Card"
      @click="goToJobCard()"
    />
  </div>
</template>

<script setup>
function goToBookings() {
  window.location.href = '/app/Service Booking'
}

function goToJobCard() {
  window.location.href = '/app/Service Job Card'
}
</script>