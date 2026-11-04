<template>
  <div v-if="showDialog" class="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center" @click.self="$emit('closeDialog')">
    <section class="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-t-xl bg-white p-5 shadow-xl sm:rounded-xl"
      role="dialog" aria-modal="true" aria-label="Create Booking">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-bold">New Booking</h2>
        <button type="button" class="sm-control" :disabled="saving" @click="$emit('closeDialog')">✕</button>
      </div>
      <form class="grid grid-cols-1 gap-3 sm:grid-cols-2" @submit.prevent="submit">
        <label class="sm-label col-span-full"><span>Customer *</span>
          <select v-model="customer" required class="sm-input">
            <option value="" disabled>Select customer</option>
            <option v-for="item in customers" :key="item.name" :value="item.name">{{ item.customer_name || item.name }}</option>
          </select>
        </label>
        <label class="sm-label col-span-full"><span>Service Vehicle *</span>
          <select v-model="vehicle" required class="sm-input" :disabled="!customer">
            <option value="" disabled>Select vehicle</option>
            <option v-for="item in availableVehicles" :key="item.name" :value="item.name">{{ item.registration_number || item.name }}</option>
          </select>
        </label>
        <label class="sm-label"><span>Date *</span><input v-model="date" class="sm-input" type="date" required /></label>
        <label class="sm-label"><span>Start Time</span><input v-model="time" class="sm-input" type="time" /></label>
        <label class="sm-label col-span-full"><span>Workshop *</span>
          <select v-model="workshopValue" class="sm-input" required>
            <option value="" disabled>Select workshop</option>
            <option v-for="item in workshops" :key="item.name" :value="item.name">{{ item.name }}</option>
          </select>
        </label>
        <label v-if="bayEnabled" class="sm-label col-span-full"><span>Bay (optional)</span>
          <select v-model="bay" class="sm-input">
            <option value="">No Bay</option>
            <option v-for="item in matchingBays" :key="item.name" :value="item.name">{{ item.name }}</option>
          </select>
        </label>
        <label class="sm-label col-span-full"><span>Service Description</span>
          <textarea v-model="description" class="sm-input" rows="2" maxlength="1000"></textarea>
        </label>
        <div class="col-span-full text-xs text-gray-500">
          For a new customer or vehicle, use its native Frappe form first, then return to the calendar.
        </div>
        <div v-if="loadError || error" class="col-span-full text-sm text-red-700" role="alert">{{ loadError || error }}</div>
        <footer class="col-span-full mt-3 flex justify-end gap-2">
          <button type="button" class="sm-control" :disabled="saving" @click="$emit('closeDialog')">Cancel</button>
          <button type="submit" class="sm-primary" :disabled="loading || saving">{{ saving ? 'Creating…' : 'Create Booking' }}</button>
        </footer>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
const props = defineProps({
  showDialog: Boolean,
  booking_date: String,
  workshop: String,
})
const emit = defineEmits(['closeDialog', 'refreshData'])
const customer = ref('')
const vehicle = ref('')
const date = ref('')
const time = ref('')
const workshopValue = ref('')
const bay = ref('')
const description = ref('')
const customers = ref([])
const vehicles = ref([])
const workshops = ref([])
const bays = ref([])
const bayEnabled = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const loadError = ref('')
const availableVehicles = computed(() => vehicles.value.filter((item) => item.customer === customer.value))
const matchingBays = computed(() => bays.value.filter((item) => item.service_workshop === workshopValue.value))
watch(customer, () => { vehicle.value = '' })
watch(workshopValue, () => { bay.value = '' })
watch(() => props.showDialog, async (open) => {
  if (!open) return
  date.value = props.booking_date || ''
  workshopValue.value = props.workshop || ''
  customer.value = ''
  vehicle.value = ''
  bay.value = ''
  description.value = ''
  time.value = ''
  error.value = ''
  loadError.value = ''
  loading.value = true
  try {
    const [customerRows, vehicleRows, workshopRows, settings] = await Promise.all([
      frappeRequest({url: 'frappe.client.get_list', method: 'GET',
        params: {doctype: 'Customer', fields: JSON.stringify(['name', 'customer_name']), limit_page_length: 500}}),
      frappeRequest({url: 'frappe.client.get_list', method: 'GET',
        params: {doctype: 'Service Vehicle', fields: JSON.stringify(['name', 'registration_number', 'customer']), limit_page_length: 500}}),
      frappeRequest({url: 'frappe.client.get_list', method: 'GET',
        params: {doctype: 'Service Workshop', fields: JSON.stringify(['name']), limit_page_length: 500}}),
      frappeRequest({url: 'frappe.client.get', method: 'GET', params: {doctype: 'Service Settings', name: 'Service Settings'}}),
    ])
    customers.value = customerRows || []
    vehicles.value = vehicleRows || []
    workshops.value = workshopRows || []
    bayEnabled.value = Boolean(Number(settings.enable_bay_management))
    bays.value = bayEnabled.value
      ? await frappeRequest({url: 'frappe.client.get_list', method: 'GET',
          params: {doctype: 'Bay', fields: JSON.stringify(['name', 'service_workshop']), limit_page_length: 500}})
      : []
  } catch (e) {
    loadError.value = e.messages?.join(' ') || e.message || 'Unable to load booking options.'
  } finally {
    loading.value = false
  }
})
async function submit() {
  if (loading.value || saving.value) return
  error.value = ''
  saving.value = true
  try {
    await frappeRequest({
      url: 'servicems.api.calendar.create_booking',
      method: 'POST',
      params: {booking: {
        customer: customer.value, service_vehicle: vehicle.value,
        booking_date: date.value, booking_time: time.value,
        workshop: workshopValue.value, bay: bayEnabled.value ? bay.value : '',
        service_description: description.value,
      }},
    })
    emit('closeDialog')
    emit('refreshData')
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message || 'Unable to create booking.'
  } finally {
    saving.value = false
  }
}
</script>
<style scoped>
.sm-control { border:1px solid #dce2ec; border-radius:6px; padding:8px 11px; font-size:13px; }
.sm-primary { background:#bc2230; color:#fff; border-radius:7px; padding:9px 14px; font-weight:700; font-size:13px; }
.sm-primary:disabled { opacity:.55; }
.sm-input { display:block; width:100%; border:1px solid #dce2ec; border-radius:6px; padding:8px 10px; font-size:13px; background:white; }
.sm-label span { font-size:12px; color:#55647b; display:block; margin-bottom:3px; }
</style>
