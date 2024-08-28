<template>
  <div class="max-w-3xl py-12 mx-auto">
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Dialog } from 'frappe-ui'
import { createResource } from 'frappe-ui'
import { session } from '../data/session'

const ping = createResource({
  url: 'ping',
  auto: true,
})

const showDialog = ref(false)
</script>