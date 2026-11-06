<template>
  <div
    v-if="showDialog"
    class="sm-modal"
    @click.self="close"
    @keydown.esc="close"
  >
    <section
      class="sm-booking-dialog"
      role="dialog"
      aria-modal="true"
      aria-label="Create Booking"
      tabindex="-1"
    >
      <header class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">New Booking</h2>
        <button
          type="button"
          class="sm-control"
          :disabled="saving"
          aria-label="Close booking form"
          @click="close"
        >
          ✕
        </button>
      </header>
      <form
        class="grid grid-cols-1 gap-3 sm:grid-cols-2"
        @submit.prevent="submit"
      >
        <label
          v-if="context.can_create_customer"
          class="col-span-full flex items-center gap-2 text-sm"
        >
          <input v-model="newCustomerMode" type="checkbox" :disabled="saving" />
          Create new Customer
        </label>
        <template v-if="newCustomerMode">
          <label class="sm-label col-span-full"
            ><span>Customer Name *</span
            ><input
              v-model="newCustomer.customer_name"
              class="sm-input"
              required
          /></label>
          <label class="sm-label"
            ><span>Customer Type *</span
            ><select v-model="newCustomer.customer_type" class="sm-input">
              <option>Individual</option>
              <option>Company</option>
              <option>Partnership</option>
            </select></label
          >
          <label class="sm-label"
            ><span>Customer Group *</span
            ><RecordLink
              v-model="newCustomer.customer_group"
              doctype="Customer Group"
              label="Customer Group"
              :filters="{ is_group: 0 }"
              required
          /></label>
          <label class="sm-label"
            ><span>Territory *</span
            ><RecordLink
              v-model="newCustomer.territory"
              doctype="Territory"
              label="Territory"
              :filters="{ is_group: 0 }"
              required
          /></label>
          <label class="sm-label"
            ><span>Mobile number</span
            ><input v-model="newCustomer.mobile_no" type="tel" class="sm-input"
          /></label>
          <label
            v-for="field in context.customer_required_fields || []"
            :key="field.fieldname"
            class="sm-label"
          >
            <span>{{ field.label }} *</span>
            <select
              v-if="field.fieldtype === 'Select'"
              v-model="newCustomer[field.fieldname]"
              class="sm-input"
              required
            >
              <option value="" disabled>Select {{ field.label }}</option>
              <option
                v-for="option in field.options.split('\n').filter(Boolean)"
                :key="option"
              >
                {{ option }}
              </option>
            </select>
            <RecordLink
              v-else-if="field.fieldtype === 'Link'"
              v-model="newCustomer[field.fieldname]"
              :doctype="field.options"
              :label="field.label"
              required
            />
            <input
              v-else
              v-model="newCustomer[field.fieldname]"
              :type="field.fieldtype === 'Date' ? 'date' : 'text'"
              class="sm-input"
              required
            />
          </label>
        </template>
        <label v-else class="sm-label col-span-full"
          ><span>Customer *</span
          ><RecordLink
            v-model="customer"
            doctype="Customer"
            label="Customer"
            required
        /></label>
        <label
          v-if="context.can_create_vehicle"
          class="col-span-full flex items-center gap-2 text-sm"
          ><input
            v-model="newVehicleMode"
            type="checkbox"
            :disabled="saving || newCustomerMode"
          />
          Create new Vehicle</label
        >
        <template v-if="newVehicleMode">
          <label class="sm-label"
            ><span>Registration Number *</span
            ><input
              v-model="newVehicle.registration_number"
              class="sm-input"
              required
          /></label>
          <label class="sm-label"
            ><span>Vehicle Model *</span
            ><RecordLink
              v-model="newVehicle.vehicle_model"
              doctype="Vehicle Model"
              label="Vehicle Model"
              required
          /></label>
          <label class="sm-label"
            ><span>Engine Number</span
            ><input v-model="newVehicle.engine_number" class="sm-input"
          /></label>
          <label class="sm-label"
            ><span>Chassis Number</span
            ><input v-model="newVehicle.chassis_number" class="sm-input"
          /></label>
        </template>
        <label v-else class="sm-label col-span-full"
          ><span>Service Vehicle *</span
          ><RecordLink
            v-model="vehicle"
            doctype="Service Vehicle"
            label="Service Vehicle"
            :filters="{ customer }"
            :disabled="!customer || newCustomerMode"
            required
        /></label>
        <label class="sm-label"
          ><span>Date *</span
          ><input v-model="date" class="sm-input" type="date" required
        /></label>
        <label class="sm-label"
          ><span>Start Time</span
          ><input v-model="time" class="sm-input" type="time"
        /></label>
        <label class="sm-label col-span-full"
          ><span>Workshop *</span
          ><RecordLink
            v-model="workshopValue"
            doctype="Service Workshop"
            label="Workshop"
            required
        /></label>
        <label
          v-if="context.bay_management_enabled"
          class="sm-label col-span-full"
          ><span>Bay (optional)</span
          ><RecordLink
            v-model="bay"
            doctype="Bay"
            label="Bay"
            placeholder="No Bay"
            :filters="{ service_workshop: workshopValue }"
            :disabled="!workshopValue"
        /></label>
        <label class="sm-label col-span-full"
          ><span>Service Description</span
          ><textarea
            v-model="description"
            class="sm-input"
            rows="2"
            maxlength="1000"
          ></textarea>
        </label>
        <p class="col-span-full text-xs text-gray-500">
          Start time in {{ context.timezone || 'site timezone' }}. New records
          are saved together with the booking.
        </p>
        <div
          v-if="loadError || error"
          class="col-span-full text-sm text-red-700"
          role="alert"
        >
          {{ loadError || error }}
        </div>
        <footer class="col-span-full mt-2 flex justify-end gap-2">
          <button
            type="button"
            class="sm-control"
            :disabled="saving"
            @click="close"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="sm-primary"
            :disabled="loading || saving"
          >
            {{ saving ? 'Creating…' : 'Create Booking' }}
          </button>
        </footer>
      </form>
    </section>
  </div>
</template>
<script setup>
import { nextTick, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import RecordLink from './CalendarRecordLink.vue'
const props = defineProps({
  showDialog: Boolean,
  booking_date: String,
  workshop: String,
})
const emit = defineEmits(['closeDialog', 'refreshData'])
const customer = ref(''),
  vehicle = ref(''),
  date = ref(''),
  time = ref(''),
  workshopValue = ref(''),
  bay = ref(''),
  description = ref('')
const newCustomerMode = ref(false),
  newVehicleMode = ref(false)
const newCustomer = ref({}),
  newVehicle = ref({}),
  context = ref({})
const loading = ref(false),
  saving = ref(false),
  error = ref(''),
  loadError = ref('')
let opener
function close() {
  if (!saving.value) {
    emit('closeDialog')
    nextTick(() => opener?.focus())
  }
}
watch(customer, () => {
  vehicle.value = ''
})
watch(workshopValue, () => {
  bay.value = ''
})
watch(newCustomerMode, (on) => {
  if (on) {
    newVehicleMode.value = true
    customer.value = ''
    vehicle.value = ''
  }
})
watch(newVehicleMode, () => {
  vehicle.value = ''
})
watch(
  () => props.showDialog,
  async (open) => {
    if (!open) return
    opener = document.activeElement
    date.value = props.booking_date || ''
    time.value = ''
    workshopValue.value = props.workshop || ''
    customer.value = ''
    vehicle.value = ''
    bay.value = ''
    description.value = ''
    newCustomerMode.value = false
    newVehicleMode.value = false
    newCustomer.value = {
      customer_name: '',
      customer_type: 'Individual',
      customer_group: '',
      territory: '',
      mobile_no: '',
    }
    newVehicle.value = {
      registration_number: '',
      vehicle_model: '',
      engine_number: '',
      chassis_number: '',
    }
    error.value = ''
    loadError.value = ''
    loading.value = true
    try {
      context.value = await frappeRequest({
        url: 'servicems.api.calendar.get_booking_context',
        method: 'GET',
      })
      for (const field of context.value.customer_required_fields || [])
        newCustomer.value[field.fieldname] = ''
      await nextTick()
      document.querySelector('.sm-booking-dialog input:not(:disabled)')?.focus()
    } catch (e) {
      loadError.value =
        e.messages?.join(' ') || e.message || 'Unable to load booking options.'
    } finally {
      loading.value = false
    }
  }
)
async function submit() {
  if (loading.value || saving.value) return
  error.value = ''
  saving.value = true
  try {
    await frappeRequest({
      url: 'servicems.api.calendar.create_booking',
      method: 'POST',
      params: {
        booking: {
          customer: newCustomerMode.value ? '' : customer.value,
          service_vehicle: newVehicleMode.value ? '' : vehicle.value,
          booking_date: date.value,
          booking_time: time.value,
          workshop: workshopValue.value,
          bay: context.value.bay_management_enabled ? bay.value : '',
          service_description: description.value,
        },
        new_customer: newCustomerMode.value ? { ...newCustomer.value } : null,
        new_vehicle: newVehicleMode.value ? { ...newVehicle.value } : null,
      },
    })
    emit('closeDialog')
    emit('refreshData')
  } catch (e) {
    error.value =
      e.messages?.join(' ') || e.message || 'Unable to create booking.'
  } finally {
    saving.value = false
  }
}
</script>
<style scoped>
.sm-modal {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: #0006;
  overflow: hidden;
}
.sm-booking-dialog {
  width: 100%;
  max-width: 576px;
  max-height: 100%;
  overflow-y: auto;
  overscroll-behavior: contain;
  border-radius: 10px;
  padding: 20px;
  background: white;
  box-shadow: 0 12px 40px #0003;
}
.sm-control {
  border: 1px solid #dce2ec;
  border-radius: 6px;
  padding: 8px 11px;
  font-size: 13px;
  background: white;
}
.sm-primary {
  background: #171717;
  color: white;
  border-radius: 6px;
  padding: 9px 14px;
  font-weight: 600;
  font-size: 13px;
}
.sm-primary:disabled {
  opacity: 0.55;
}
.sm-input {
  display: block;
  width: 100%;
  min-width: 0;
  border: 1px solid #dce2ec;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  background: white;
}
.sm-label {
  min-width: 0;
}
.sm-label span {
  font-size: 12px;
  color: #55647b;
  display: block;
  margin-bottom: 3px;
}
@media (max-width: 639px) {
  .sm-modal {
    padding: 8px;
    align-items: flex-end;
  }
  .sm-booking-dialog {
    padding: 16px;
  }
}
</style>
