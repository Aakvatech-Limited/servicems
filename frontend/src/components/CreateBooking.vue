<template>
    <Dialog :model-value="localShowDialog" @update:model-value="updateDialogVisibility" :options="{ size: '5xl' }">
        <template #body>
            <div class="bg-white px-4 pb-6 pt-5 sm:px-6">
                <div class="mb-5 flex gap-36 items-center justify-around">
                    <div class="ml-60 w-112">
                        <h3 class="text-2xl text-center font-semibold leading-6 text-gray-900">
                            Create Booking
                        </h3>
                    </div>
                    <div class="flex justify-end w-12">
                        <Button variant="ghost" class="w-7" @click="showDialog = false">
                            <FeatherIcon name="x" class="h-7 w-7" />
                        </Button>
                    </div>
                </div>
                <div v-if="isBookingCreating" class="text-center py-4 text-gray-500">{{ statusMessage }}</div>
                <div>
                    <FieldMap v-if="sections" :sections="sections" :data="booking" />
                    <ErrorMessage class="mt-4 text-lg font-bold" v-if="error" :message="error" />
                </div>
            </div>
            <div class="px-4 pb-7 pt-4 lg:px-7">
                <div class="flex flex-row-reverse gap-2 w-full">
                    <button
                        class="w-24 h-10 text-sm font-medium text-white bg-blue-500 rounded-md hover:bg-cyan-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        :loading="isBookingCreating"
                        @click="create_booking_docs()"
                    >
                        Create
                    </button>
                </div>
            </div>
        </template>
    </Dialog>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { ErrorMessage, createResource } from 'frappe-ui'
import FieldMap from '../components/FieldMap.vue'
import { useToast } from 'vue-toastification';


const isBookingCreating = ref(false)
const statusMessage = ref('');
const error = ref(null)

const props = defineProps({
  showDialog: Boolean,
  bay: String,
  booking_date: Date
})

const toast = useToast();
const emit = defineEmits(['closeDialog'])

const localShowDialog = ref(props.showDialog)

function updateDialogVisibility(newVal) {
    localShowDialog.value = newVal;
    emit('update:showDialog', newVal);
}

watch(() => props.showDialog, (newVal) => {
  localShowDialog.value = newVal
})

watch (() => props.bay, (newVal) => {
  booking['Service Booking']['bay'] = newVal
})

watch (() => props.booking_date, (newVal) => {
  booking['Service Booking']['booking_date'] = newVal
})

const closeDialog = () => {
  localShowDialog.value = false
  emit('closeDialog')
}

function showToast(message, type) {    
    const toastTypes = ['success', 'info', 'warning', 'error'];

    if (toastTypes.includes(type) && toast[type]) {
        toast[type](message);
    } else {
        toast(message);
    }
}

const booking_doc = createResource({
    url: 'frappe.client.insert',
    method: 'POST',
    makeParams() {
        return {
            doc: {
                doctype: 'Service Booking',
                ...booking['Service Booking']
            }
        }
    },
    validate(params) {
        error.value = null
        if (!params.doc.customer) {
            error.value = 'Customer is required'
            showToast('Customer is required', 'error')
            return error.value
        }
        if (!params.doc.service_vehicle && !params.doc.is_new_vehicle) {
            error.value = 'Service Vehicle is required'
            showToast('Service Vehicle is required', 'error')
            return error.value
        }
        if (!params.doc.booking_date) {
            error.value = 'Booking Date is required'
            showToast('Booking Date is required', 'error')
            return error.value
        }
        if (!params.doc.booking_time) {
            error.value = 'Booking Time is required'
            showToast('Booking Time is required', 'error')
            return error.value
        }
        // if (!params.doc.workshop) {
        //     error.value = 'Workshop is required'
        //     return error.value
        // }
        if (!params.doc.bay) {
            error.value = 'Bay is required'
            showToast('Bay is required', 'error')
            return error.value
        }

        isBookingCreating.value = true
    },
    onSuccess: (data) => {
        isBookingCreating.value = false
        showToast('Booking created successfully', 'success')
        closeDialog()
        resetBooking()
        emit('refreshData');
    },
    onError: (err) => {
        isBookingCreating.value = false
        if (!err.messages) {
            error.value = err.message
            return
        }
        error.value = err.messages.join('\n')
    }
})

const customer_doc = createResource({
    url: 'frappe.client.insert',
    method: 'POST',
    makeParams() {
        return {
            doc: {
                doctype: 'Customer',
                ...booking['Customer']
            }
        }
    },
    validate(params) {
        error.value = null
        if (!params.doc.customer_name) {
            error.value = 'Customer Name is required'
            showToast('Customer Name is required', 'error')
            return error.value
        }
        if (!params.doc.customer_type) {
            error.value = 'Customer Type is required'
            showToast('Customer Type is required', 'error')
            return error.value
        }
        if (!params.doc.customer_group) {
            error.value = 'Customer Group is required'
            showToast('Customer Group is required', 'error')
            return error.value
        }
        if (!params.doc.territory) {
            error.value = 'Territory is required'
            showToast('Territory is required', 'error')
            return error.value
        }
    },
    onSuccess: (data) => {
        booking['Service Booking']['customer'] = data.name
        booking['Service Vehicle']['customer'] = data.name

        showToast('Customer created successfully', 'success')
    },
    onError: (err) => {
        if (!err.messages) {
            error.value = err.message
            showToast(error.value, "error")
            return
        }
        error.value = err.messages.join('\n')

        showToast(error.value, "error")
    }
})

const vehicle_doc = createResource({
    url: 'frappe.client.insert',
    method: 'POST',
    makeParams() {
        return {
            doc: {
                doctype: 'Service Vehicle',
                ...booking['Service Vehicle']
            }
        }
    },
    validate(params) {
        error.value = null
        if (!params.doc.registration_number) {
            error.value = 'Registration Number is required'
            showToast('Registration Number is required', 'error')
            return error.value
        }
        if (!params.doc.customer) {
            error.value = 'Customer is required'
            showToast('Customer is required', 'error')
            return error.value
        }
        if (!params.doc.vehicle_model) {
            error.value = 'Vehicle Model is required'
            showToast('Vehicle Model is required', 'error')
            return error.value
        }
    },
    onSuccess: (data) => {
        booking['Service Booking']['service_vehicle'] = data.name
        showToast('Vehicle created successfully', 'success')
    },
    onError: (err) => {
        if (!err.messages) {
            error.value = err.message
            showToast(error.value, "error")
            return
        }
        error.value = err.messages.join('\n')
        showToast(error.value, "error")
    }
})

async function create_booking_docs() {
    isBookingCreating.value = true;
    error.value = null;

    try {
        if (booking['Service Booking']['is_new_customer']) {
            statusMessage.value = 'Creating customer...';
            await customer_doc.submit();
        }

        if (booking['Service Booking']['is_new_vehicle']) {
            statusMessage.value = 'Creating vehicle...';
            await vehicle_doc.submit();
        }

        statusMessage.value = 'Creating booking...';
        await booking_doc.submit();

    } catch (err) {
        error.value = 'Error while creating booking documents';
        showToast(error.value, "error");
    } finally {
        isBookingCreating.value = false;
    }
}


function resetBooking() {
    booking["Service Booking"] = {
        "is_new_customer": false,
        "customer": "",
        "is_new_vehicle": false,
        "service_vehicle": "",
        "booking_date": "",
        "booking_time": "",
        // "workshop": "",
        "bay": "",
        "service_description": "",
        "disabled": false
    }

    booking["Customer"] = {
        "customer_name": "",
        "customer_type": "",
        "customer_group": "",
        "territory": "",
        "tax_id": "",
        "mobile_no": "",
        "disabled": false
    }

    booking["Service Vehicle"] = {
        "registration_number": "",
        "customer": "",
        "vehicle_model": "",
        "make": "",
        "type": "",
        "engine_number": "",
        "chassis_number": "",
        "disabled": false
    }
}

const booking = reactive({
    "Service Booking": {
        "is_new_customer": false,
        "customer": "",
        "is_new_vehicle": false,
        "service_vehicle": "",
        "booking_date": "",
        "booking_time": "",
        // "workshop": "",
        "bay": "",
        "service_description": "",
        "disabled":false
    },
    "Customer": {
        "customer_name": "",
        "customer_type": "",
        "customer_group": "",
        "territory": "",
        "tax_id": "",
        "mobile_no": "",
        "disabled":false
    },
    "Service Vehicle": {
        "registration_number": "",
        "customer": "",
        "vehicle_model": "",
        "make": "",
        "type": "",
        "engine_number": "",
        "chassis_number": "",
        "disabled":false
    }
})

const sections = [
    {
        "label":"Booking Details",
        "doctype":"Service Booking",
        "fields":[
            {"name": "is_new_customer", "label": "Is New Customer", "type": "Check", "placeholder": "Is New Customer", "reqd": false},
            {"name": "customer", "label": "Customer", "type": "Link", "placeholder": "Customer", "options": "Customer", "reqd": true},
            {"name": "is_new_vehicle", "label": "Is New Vehicle", "type": "Check", "placeholder": "Is New Vehicle", "reqd": false},
            {"name": "service_vehicle", "label": "Service Vehicle", "type": "Link", "placeholder": "Service Vehicle", "options": "Service Vehicle", "reqd": true},
            {"name": "booking_date", "label": "Booking Date", "type": "Date", "placeholder": "Booking Date", "reqd": true},
            {"name": "booking_time", "label": "Booking Time", "type": "Time", "placeholder": "Booking Time", "reqd": true},
            // {"name": "workshop", "label": "Workshop", "type": "Link", "placeholder": "Workshop", "options": "Customer", "reqd": true },
            {"name": "bay", "label": "Bay", "type": "Link", "placeholder": "Bay", "options": "Bay", "reqd": true},
            {"name": "service_description", "label": "Service Description", "type": "Small Text", "placeholder": "Service Description", "reqd": false},
        ],
        "hideLabel":false
    },
    {
        "label":"Customer Details",
        "doctype":"Customer",
        "fields":[
            {"name": "customer_name", "label": "Customer Name", "type": "Data", "placeholder": "Customer Name", "reqd": true},
            {
                "name": "customer_type", "label": "Customer Type", "type": "Select", "placeholder": "Customer Type",
                "options": ["Individual", "Corporate", "Government", "Non-profit"],
                "reqd": true
            },
            {"name": "customer_group", "label": "Customer Group", "type": "Link", "placeholder": "Customer Group", "options": "Customer Group", "reqd": true},
            {"name": "territory", "label": "Territory", "type": "Link", "placeholder": "Territory", "options": "Territory", "reqd": true},
            {"name": "tax_id", "label": "TIN", "type": "Data", "placeholder": "TIN", "reqd": false},
            {"name": "mobile_no", "label": "Mobile No", "type": "Data", "placeholder": "Mobile No", "reqd": false},
        ],
        "hideLabel":false,
        "hideBorder":false
    },
    {
        "label":"Vehicle Details",
        // "columns":2,
        "doctype":"Service Vehicle",
        "fields":[
            {"name": "registration_number", "label": "Registration Number", "type": "Data", "placeholder": "Registration Number", "reqd": true},
            {"name": "customer", "label": "Customer", "type": "Link", "placeholder": "Customer", "options": "Customer", "reqd": true},
            {"name": "vehicle_model", "label": "Vehicle Model", "type": "Data", "placeholder": "Vehicle Model", "options": "Vehicle Model", "reqd": true},
            {"name": "make", "label": "Make", "type": "Data", "placeholder": "Make", "reqd": false},
            {"name": "type", "label": "Type", "type": "Data", "placeholder": "Type", "reqd": false},
            {"name": "engine_number", "label": "Engine Number", "type": "Data", "placeholder": "Engine Number", "reqd": false},
            {"name": "chassis_number", "label": "Chassis Number", "type": "Data", "placeholder": "Chassis Number", "reqd": false},
        ],
        "hideLabel":false,
        "hideBorder":false
    }
]

</script>