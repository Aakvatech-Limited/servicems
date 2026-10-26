<template>
  <Dialog
    :model-value="showDialog"
    :options="{ title: 'Create Booking', size: '5xl' }"
    :disable-outside-click-to-close="saving"
    @update:model-value="closeDialog"
  >
    <template #body-content>
      <form
        id="create-service-booking"
        class="space-y-6"
        @submit.prevent="createBooking"
      >
        <fieldset :disabled="saving" class="space-y-6">
          <div class="flex flex-wrap gap-6">
            <label class="flex items-center gap-2 text-sm font-semibold"
              ><input v-model="isNewCustomer" type="checkbox" />Is New
              Customer</label
            >
            <label class="flex items-center gap-2 text-sm font-semibold"
              ><input
                v-model="isNewVehicle"
                type="checkbox"
                :disabled="isNewCustomer"
              />Is New Vehicle</label
            >
          </div>
          <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Link
              v-if="!isNewCustomer"
              v-model="booking.customer"
              doctype="Customer"
              label="Customer *"
              placeholder="Customer"
            />
            <Link
              v-if="!isNewVehicle"
              v-model="booking.service_vehicle"
              doctype="Service Vehicle"
              label="Service Vehicle *"
              placeholder="Service Vehicle"
              :filters="booking.customer ? { customer: booking.customer } : {}"
            />
            <div>
              <label
                for="create-booking-date"
                class="mb-2 block text-sm font-semibold"
                >Booking Date *</label
              >
              <input
                id="create-booking-date"
                v-model="booking.booking_date"
                type="date"
                required
                class="form-input w-full"
              />
            </div>
            <Link
              v-model="booking.workshop"
              doctype="Service Workshop"
              label="Workshop *"
              placeholder="Workshop"
            />
            <Link
              v-if="isNewVehicle"
              v-model="newVehicle.vehicle_model"
              doctype="Vehicle Model"
              label="Vehicle Model *"
              placeholder="Vehicle Model"
            />
            <div v-else>
              <label
                for="booking-vehicle-model"
                class="mb-2 block text-sm font-semibold"
                >Vehicle Model</label
              >
              <input
                id="booking-vehicle-model"
                :value="vehicleLoading ? 'Loading...' : vehicleModel"
                readonly
                class="form-input w-full bg-gray-50"
              />
            </div>
            <div>
              <label
                for="booking-description"
                class="mb-2 block text-sm font-semibold"
                >Service Description</label
              >
              <textarea
                id="booking-description"
                v-model="booking.service_description"
                class="form-textarea w-full"
                rows="2"
              />
            </div>
          </div>
          <BookingPartyDetails
            :is-new-customer="isNewCustomer"
            :is-new-vehicle="isNewVehicle"
            :new-customer="newCustomer"
            :new-vehicle="newVehicle"
          />
        </fieldset>
        <p v-if="error" role="alert" class="text-sm text-red-700">
          {{ error }}
        </p>
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-3">
        <Button
          type="button"
          label="Cancel"
          :disabled="saving"
          @click="closeDialog"
        />
        <Button
          type="submit"
          form="create-service-booking"
          variant="solid"
          label="Create"
          :loading="saving"
          :disabled="saving || vehicleLoading"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import Link from './controls/Link.vue'
import BookingPartyDetails from './BookingPartyDetails.vue'
import { useToast } from '@/composables/useToast.js'

const props = defineProps({
  showDialog: Boolean,
  bookingDate: String,
  workshop: String,
  vehicle: String,
})
const emit = defineEmits(['closeDialog', 'refreshData'])
const { showSuccess } = useToast()
const saving = ref(false)
const error = ref('')
const isNewCustomer = ref(false)
const isNewVehicle = ref(false)
const vehicleLoading = ref(false)
const vehicleModel = ref('')
const booking = reactive({
  customer: '',
  service_vehicle: props.vehicle || '',
  booking_date: props.bookingDate,
  workshop: props.workshop || '',
  service_description: '',
})
const newCustomer = reactive({
  customer_name: '',
  customer_type: 'Individual',
  customer_group: '',
  territory: '',
  tax_id: '',
  mobile_no: '',
})
const newVehicle = reactive({
  registration_number: '',
  vehicle_model: '',
  engine_number: '',
  chassis_number: '',
})

function closeDialog() {
  if (!saving.value) emit('closeDialog')
}

async function createBooking() {
  if (saving.value || vehicleLoading.value) return
  error.value = ''
  const customer = isNewCustomer.value
    ? newCustomer.customer_name &&
      newCustomer.customer_group &&
      newCustomer.territory
    : booking.customer
  const vehicle = isNewVehicle.value
    ? newVehicle.registration_number && newVehicle.vehicle_model
    : booking.service_vehicle
  if (!customer || !vehicle || !booking.booking_date || !booking.workshop) {
    error.value =
      'Please complete Customer, Service Vehicle, Booking Date and Workshop, including the required details for a new customer or vehicle.'
    return
  }
  saving.value = true
  try {
    await frappeRequest({
      url: 'servicems.api.bookings.create_booking',
      params: {
        booking: { ...booking },
        new_customer: isNewCustomer.value ? { ...newCustomer } : null,
        new_vehicle: isNewVehicle.value ? { ...newVehicle } : null,
      },
    })
    showSuccess('Booking created successfully')
    emit('closeDialog')
    emit('refreshData')
  } catch (err) {
    error.value = err.messages?.join('\n') || err.message
  } finally {
    saving.value = false
  }
}

watch(isNewCustomer, (value) => {
  booking.customer = ''
  booking.service_vehicle = ''
  if (value) isNewVehicle.value = true
})
watch(isNewVehicle, () => {
  booking.service_vehicle = ''
})
watch(
  () => booking.customer,
  (customer, previous) => {
    if (previous && customer !== previous) booking.service_vehicle = ''
  },
)
watch(
  () => booking.service_vehicle,
  async (name, _, onCleanup) => {
    let active = true
    onCleanup(() => {
      active = false
    })
    vehicleModel.value = ''
    vehicleLoading.value = Boolean(name)
    if (!name) return
    try {
      const vehicle = await frappeRequest({
        url: 'frappe.client.get',
        method: 'GET',
        params: { doctype: 'Service Vehicle', name },
      })
      if (!active) return
      booking.customer = vehicle.customer
      vehicleModel.value = vehicle.vehicle_model || ''
    } catch (err) {
      if (active) error.value = err.messages?.join('\n') || err.message
    } finally {
      if (active) vehicleLoading.value = false
    }
  },
  { immediate: true },
)
</script>
