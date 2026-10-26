<template>
  <div
    class="w-full shrink-0 bg-gray-200 flex flex-row items-center gap-3 p-4 md:min-h-screen md:w-48 md:flex-col md:items-start md:p-6 lg:w-60"
  >
    <div
      v-if="settings.doc && settings.doc.app_logo"
      class="w-20 h-auto shrink-0 flex items-center justify-center md:mb-5"
      @click="goToHome()"
    >
      <img
        :src="settings.doc.app_logo"
        alt="logo"
        class="w-full rounded-full"
      />
    </div>
    <Button
      class="w-full hover:bg-green-500/50 text-black font-bold py-4 px-3 rounded border border-gray-300 md:mb-5"
      label="Bookings"
      @click="goToBookings()"
    />

    <Button
      class="w-full hover:bg-green-500/50 text-black font-bold py-4 px-3 rounded border border-gray-300"
      label="Job Card"
      @click="goToJobCard()"
    />
  </div>
</template>

<script setup>
import { createDocumentResource } from 'frappe-ui'
import { useToast } from '@/composables/useToast.js'

const { handleResourceError } = useToast()

function goToBookings() {
  window.location.href = '/app/service-booking'
}

function goToJobCard() {
  window.location.href = '/app/service-job-card'
}

function goToHome() {
  window.location.href = '/app/service-ms'
}

let settings = createDocumentResource({
  doctype: 'Navbar Settings',
  name: 'Navbar Settings',

  onError: (err) => {
    handleResourceError(err)
  },
})
</script>
