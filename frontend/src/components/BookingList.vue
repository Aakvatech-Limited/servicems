<template>
    <div class="mb-6">
        <DateFilter :filters="filters" />
    </div>
    <div class="scroll h-[600px] overflow-y-auto">
        <div v-if="loading" class="text-center py-4 text-gray-500">Loading bookings...</div>

        <div v-for="(bookings, date) in weeklyBookings" :key="date" class="mb-5">
            <div class="border border-gray-300 rounded-md p-4 relative">
                <h1 class="flex shadow-lg shadow-green-500 font-bold mb-8 text-center h-7 text-2xl">
                    {{ date }}
                </h1>

                <div class="flex items-center justify-between relative">
                    <button
                        @click="scrollLeft(date)"
                        class="absolute left-0 top-1/2 transform -translate-y-1/2 bg-gray-500 px-2 text-white font-bold text-xl rounded-l-md z-10"
                        v-if="bookings.length > 4"
                    >
                        &lt;
                    </button>

                    <div :id="`container-${date}`" class="flex overflow-x-hidden gap-4 px-8 h-40 custom-scroll-hidden relative">
                        <div
                            v-for="item in bookings"
                            :key="item.name"
                            :class="[
                                !item.status ? 'bg-white-overlay-500 border-0 shadow-xl shadow-cyan-500/50 font-sans' : 'bg-blue-300 border-blue-300 shadow-lg shadow-cyan-500/50 font-mono'
                            ]"
                            class="w-[140px] h-[150px] flex-shrink-0 rounded-md shadow-md p-2 flex flex-col justify-between"
                        >

                            <div class="flex-1 overflow-hidden text-ellipsis whitespace-nowrap mt-2 text-center">
                                <p class="font-bold text-base">{{ item.bay_name }}</p>
                                <p v-if="item.status"
                                    class="rounded-md bg-orange-200 text-sm text-orange-900 ring-1 ring-inset ring-orange-500/10">
                                    Status: {{ item.status === 'In Progress' ? 'Progress' : item.status }}
                                </p>
                            </div>
                            <div class="translate-x-3/4 mb-6" >
                                <div 
                                    class="bg-gray-400 text-black rounded-full w-9 h-9 flex items-center justify-center text-5xl font-bold hover:bg-blue-700/50"
                                    @click="openBookingDoc(item.bay_name, date)"
                                >
                                    {{ item.count || 0 }}
                                </div>
                            </div>

                            <div class="flex justify-center mt-auto">
                                <button
                                    class="bg-gray-400 text-black font-bold px-2 rounded-md text-base w-full h-5"
                                    @click="addBooking(item.bay_name, date)"
                                    >
                                    +Add
                                </button>
                            </div>
                        </div>
                    </div>

                    <button
                        @click="scrollRight(date)"
                        class="absolute right-0 top-1/2 transform -translate-y-1/2 bg-gray-500 px-2 text-white font-bold text-xl rounded-r-md z-10"
                        v-if="bookings.length > 4"
                    >
                        &gt;
                    </button>
                </div>
            </div>
        </div>
        <CreateBooking 
            :showDialog="showDialog" 
            :bay="_bayName" 
            :booking_date="booking_date" 
            @closeDialog="showDialog = false"
            @refreshData="refreshBayData"
        />
    </div>
</template>


<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { createResource, toast } from 'frappe-ui'
import { addDays, format, differenceInDays } from 'date-fns'
import CreateBooking from '@/components/CreateBooking.vue'
import DateFilter from '@/components/DateFilter.vue'
import { useToast } from 'vue-toastification'

const today = new Date()
const lastcount = ref(0)
const loading = ref(true)
const showDialog = ref(false)
const _bayName = ref('')
const booking_date = ref(today.value)

const filters = reactive({
    from_date: today.value,
    to_date: '',
    workshop: '',
})

const tos = useToast();

watch(() => filters, async () => {
    loading.value = true
    await bay_data.fetch()
    loading.value = false
}, { deep: true })

const bay_data = createResource({
    url: 'servicems.api.api.get_service_bays',
    method: 'GET',
    auto: true,
    cache: 'bookings',
    makeParams() {
        return {
            from_date: filters.from_date || format(today.value, 'yyyy-MM-dd'),
            to_date: filters.to_date,
            workshop: filters.workshop,
        }
    },
    validate(params) {
    },
    onSuccess: (data) => {
    },
    onError: (err) => {
        if (!err.messages) {
            tos.error(err.message)
            return
        }
        tos.error(err.messages.join('\n'))
    }
})

const weeklyBookings = computed(() => {
    const dates = {};

    today.value = filters.from_date ? new Date(filters.from_date) : new Date();
    lastcount.value = filters.to_date ? differenceInDays(new Date(filters.to_date), today.value) : 6;

    for (let i = 0; i <= lastcount.value; i++) {
        const currentDate = format(addDays(today.value, i), 'EE, yyyy-MM-dd');
        dates[currentDate] = [];
    }

    const bayDataList = bay_data.data;
    const allBays = bayDataList.filter(item => item.bay_name).map(item => ({
        bay_name: item.bay_name,
        workshop: item.workshop,
        count: 0,
        status: '',
        customer: '',
        booking_time: '',
        booking_date: ''
    }));

    for (const dateKey in dates) {
        const uniqueBays = new Map();
        allBays.forEach(bay => {
            uniqueBays.set(bay.bay_name, bay);
        });
        dates[dateKey] = Array.from(uniqueBays.values());
    }

    if (Array.isArray(bayDataList)) {
        bayDataList.forEach((item) => {
            const itemDate = item.booking_date;
            if (itemDate) {
                const formattedItemDate = format(itemDate, 'EE, yyyy-MM-dd');
                if (dates[formattedItemDate]) {
                    const bayIndex = dates[formattedItemDate].findIndex(bay => bay.bay_name === item.bay_name);
                    if (bayIndex !== -1) {
                        dates[formattedItemDate][bayIndex] = item;
                    } else {
                        dates[formattedItemDate].push(item);
                    }
                }
            }
        });
    }

    return dates;
});


function openBookingDoc(bay_name, date) {
    const bDate = format(date, 'yyyy-MM-dd')
    window.location.href = '/app/service-booking?bay=' + bay_name + '&booking_date=' + bDate
}

function addBooking(bay_name, date) {
    showDialog.value = true
    _bayName.value = bay_name
    booking_date.value = format(date, 'yyyy-MM-dd')
}

const scrollLeft = (date) => {
    const container = document.getElementById(`container-${date}`)
    container.scrollBy({ left: -300, behavior: 'smooth' })
}

async function refreshBayData() {
    loading.value = true;
    await bay_data.fetch().then(() => {
        loading.value = false;
    }).catch(() => {
        loading.value = false;
    });
}

const scrollRight = (date) => {
    const container = document.getElementById(`container-${date}`)
    container.scrollBy({ left: 300, behavior: 'smooth' })
}

onMounted(async () => {
    await bay_data.fetch()
    loading.value = false
})

</script>

<style scoped>
.custom-scroll-hidden {
    scrollbar-width: none;
    -ms-overflow-style: none;
}
.custom-scroll-hidden::-webkit-scrollbar {
    display: none;
}
</style>
