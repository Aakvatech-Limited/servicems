<template>
  <div
    v-if="showDialog"
    class="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center"
    @click.self="$emit('closeDialog')"
  >
    <section
      class="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-t-xl bg-white p-5 shadow-xl sm:rounded-xl"
      role="dialog"
      aria-modal="true"
      aria-label="Create Booking"
    >
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-bold">New Booking</h2>
        <button
          type="button"
          class="sm-control"
          :disabled="saving"
          @click="$emit('closeDialog')"
        >
          ✕
        </button>
      </div>
      <form
        class="grid grid-cols-1 gap-3 sm:grid-cols-2"
        @submit.prevent="submit"
      >
        <label class="col-span-full flex items-center gap-2 text-sm"
          ><input
            v-model="newCustomerMode"
            type="checkbox"
            :disabled="saving"
          />
          Create new Customer</label
        >
        <template v-if="newCustomerMode">
          <label class="sm-label col-span-full"
            ><span>Customer Name *</span
            ><input
              v-model="newCustomer.customer_name"
              class="sm-input"
              required
          /></label>
          <label class="sm-label"
            ><span>Customer Type *</span>
            <select v-model="newCustomer.customer_type" class="sm-input">
              <option>Individual</option>
              <option>Company</option>
              <option>Partnership</option>
            </select>
          </label>
          <label class="sm-label"
            ><span>Customer Group *</span>
            <select
              v-model="newCustomer.customer_group"
              class="sm-input"
              required
            >
              <option value="" disabled>Select group</option>
              <option
                v-for="item in customerGroups"
                :key="item.name"
                :value="item.name"
              >
                {{ item.name }}
              </option>
            </select>
          </label>
          <label class="sm-label"
            ><span>Territory *</span>
            <select v-model="newCustomer.territory" class="sm-input" required>
              <option value="" disabled>Select territory</option>
              <option
                v-for="item in territories"
                :key="item.name"
                :value="item.name"
              >
                {{ item.name }}
              </option>
            </select>
          </label>
          <label class="sm-label"
            ><span>Mobile number</span
            ><input v-model="newCustomer.mobile_no" type="tel" class="sm-input"
          /></label>
        </template>
        <label v-else class="sm-label col-span-full"
          ><span>Customer *</span>
          <select v-model="customer" required class="sm-input">
            <option value="" disabled>Select customer</option>
            <option
              v-for="item in customers"
              :key="item.name"
              :value="item.name"
            >
              {{ item.customer_name || item.name }}
            </option>
          </select>
        </label>
        <label class="col-span-full flex items-center gap-2 text-sm"
          ><input v-model="newVehicleMode" type="checkbox" :disabled="saving" />
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
            ><span>Vehicle Model *</span>
            <select
              v-model="newVehicle.vehicle_model"
              class="sm-input"
              required
            >
              <option value="" disabled>Select model</option>
              <option
                v-for="item in vehicleModels"
                :key="item.name"
                :value="item.name"
              >
                {{ item.name }}
              </option>
            </select>
          </label>
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
          ><span>Service Vehicle *</span>
          <select
            v-model="vehicle"
            required
            class="sm-input"
            :disabled="!customer || newCustomerMode"
          >
            <option value="" disabled>Select vehicle</option>
            <option
              v-for="item in availableVehicles"
              :key="item.name"
              :value="item.name"
            >
              {{ item.registration_number || item.name }}
            </option>
          </select>
        </label>
        <label class="sm-label"
          ><span>Date *</span
          ><input v-model="date" class="sm-input" type="date" required
        /></label>
        <label class="sm-label"
          ><span>Start Time</span
          ><input v-model="time" class="sm-input" type="time"
        /></label>
        <label class="sm-label col-span-full"
          ><span>Workshop *</span>
          <select v-model="workshopValue" class="sm-input" required>
            <option value="" disabled>Select workshop</option>
            <option
              v-for="item in workshops"
              :key="item.name"
              :value="item.name"
            >
              {{ item.name }}
            </option>
          </select>
        </label>
        <label v-if="bayEnabled" class="sm-label col-span-full"
          ><span>Bay (optional)</span>
          <select v-model="bay" class="sm-input">
            <option value="">No Bay</option>
            <option
              v-for="item in matchingBays"
              :key="item.name"
              :value="item.name"
            >
              {{ item.name }}
            </option>
          </select>
        </label>
        <label class="sm-label col-span-full"
          ><span>Service Description</span>
          <textarea
            v-model="description"
            class="sm-input"
            rows="2"
            maxlength="1000"
          ></textarea>
        </label>
        <p class="col-span-full text-xs text-gray-500">
          New Customers, Vehicles and Bookings are created together; validation
          failures do not leave partial records.
        </p>
        <div
          v-if="loadError || error"
          class="col-span-full text-sm text-red-700"
          role="alert"
        >
          {{ loadError || error }}
        </div>
        <footer class="col-span-full mt-3 flex justify-end gap-2">
          <button
            type="button"
            class="sm-control"
            :disabled="saving"
            @click="$emit('closeDialog')"
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
const newCustomerMode = ref(false)
const newVehicleMode = ref(false)
const newCustomer = ref({
  customer_name: '',
  customer_type: 'Individual',
  customer_group: '',
  territory: '',
  mobile_no: '',
})
const newVehicle = ref({
  registration_number: '',
  vehicle_model: '',
  engine_number: '',
  chassis_number: '',
})
const customerGroups = ref([])
const territories = ref([])
const vehicleModels = ref([])
const customers = ref([])
const vehicles = ref([])
const workshops = ref([])
const bays = ref([])
const bayEnabled = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const loadError = ref('')
const availableVehicles = computed(() =>
  vehicles.value.filter((item) => item.customer === customer.value)
)
const matchingBays = computed(() =>
  bays.value.filter((item) => item.service_workshop === workshopValue.value)
)
watch(customer, () => {
  vehicle.value = ''
})
watch(newCustomerMode, (on) => {
  if (on) {
    newVehicleMode.value = true
    customer.value = ''
    vehicle.value = ''
  }
})
watch(newVehicleMode, (on) => {
  vehicle.value = ''
  if (!on && newCustomerMode.value) newVehicleMode.value = true
})
watch(workshopValue, () => {
  bay.value = ''
})
watch(
  () => props.showDialog,
  async (open) => {
    if (!open) return
    date.value = props.booking_date || ''
    workshopValue.value = props.workshop || ''
    customer.value = ''
    vehicle.value = ''
    bay.value = ''
    description.value = ''
    time.value = ''
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
      const [
        customerRows,
        vehicleRows,
        workshopRows,
        settings,
        groupRows,
        territoryRows,
        modelRows,
      ] = await Promise.all([
        frappeRequest({
          url: 'frappe.client.get_list',
          method: 'GET',
          params: {
            doctype: 'Customer',
            fields: JSON.stringify(['name', 'customer_name']),
            limit_page_length: 500,
          },
        }),
        frappeRequest({
          url: 'frappe.client.get_list',
          method: 'GET',
          params: {
            doctype: 'Service Vehicle',
            fields: JSON.stringify(['name', 'registration_number', 'customer']),
            limit_page_length: 500,
          },
        }),
        frappeRequest({
          url: 'frappe.client.get_list',
          method: 'GET',
          params: {
            doctype: 'Service Workshop',
            fields: JSON.stringify(['name']),
            limit_page_length: 500,
          },
        }),
        frappeRequest({
          url: 'frappe.client.get',
          method: 'GET',
          params: { doctype: 'Service Settings', name: 'Service Settings' },
        }),
        frappeRequest({
          url: 'frappe.client.get_list',
          method: 'GET',
          params: {
            doctype: 'Customer Group',
            fields: JSON.stringify(['name']),
            limit_page_length: 500,
          },
        }),
        frappeRequest({
          url: 'frappe.client.get_list',
          method: 'GET',
          params: {
            doctype: 'Territory',
            fields: JSON.stringify(['name']),
            limit_page_length: 500,
          },
        }),
        frappeRequest({
          url: 'frappe.client.get_list',
          method: 'GET',
          params: {
            doctype: 'Vehicle Model',
            fields: JSON.stringify(['name']),
            limit_page_length: 500,
          },
        }),
      ])
      customers.value = customerRows || []
      vehicles.value = vehicleRows || []
      workshops.value = workshopRows || []
      customerGroups.value = groupRows || []
      territories.value = territoryRows || []
      vehicleModels.value = modelRows || []
      bayEnabled.value = Boolean(Number(settings.enable_bay_management))
      bays.value = bayEnabled.value
        ? await frappeRequest({
            url: 'frappe.client.get_list',
            method: 'GET',
            params: {
              doctype: 'Bay',
              fields: JSON.stringify(['name', 'service_workshop']),
              limit_page_length: 500,
            },
          })
        : []
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
          bay: bayEnabled.value ? bay.value : '',
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
.sm-control {
  border: 1px solid #dce2ec;
  border-radius: 6px;
  padding: 8px 11px;
  font-size: 13px;
}
.sm-primary {
  background: #0b5be4;
  color: #fff;
  border-radius: 7px;
  padding: 9px 14px;
  font-weight: 700;
  font-size: 13px;
}
.sm-primary:disabled {
  opacity: 0.55;
}
.sm-input {
  display: block;
  width: 100%;
  border: 1px solid #dce2ec;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  background: white;
}
.sm-label span {
  font-size: 12px;
  color: #55647b;
  display: block;
  margin-bottom: 3px;
}
</style>
