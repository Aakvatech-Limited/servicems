<template>
  <div class="h-screen w-60 bg-gray-200 flex flex-col items-start p-6">
    <div
      v-if = "settings.doc && settings.doc.app_logo"
      class="mb-8 w-24 h-auto  rounded-full flex items-center justify-center mx-8"
      @click="goToHome()"
    >
      <img :src="settings.doc.app_logo" alt="logo" class="w-full rounded-full" />
    </div>
    <Button
      class="mb-8 w-full hover:bg-blue-500/50 text-black font-bold py-6 px-4 rounded border-4 border-gray-300"
      label="Bookings"
      @click="goToBookings()"
    />

    <Button 
      class="w-full hover:bg-green-500/50 text-black font-bold py-6 px-4 rounded border-4 border-gray-300"
      label="Job Card"
      @click="goToJobCard()"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { createDocumentResource } from 'frappe-ui'
import { useToast } from 'vue-toastification'


const sideTos = useToast();

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
    doctype: "Navbar Settings",
    name: "Navbar Settings",

    onError: (err) => {
          if (!err.messages) {
              tos.error(err.message)
              return
          }
          tos.error(err.messages.join('\n'))
      }
  }
)
</script>