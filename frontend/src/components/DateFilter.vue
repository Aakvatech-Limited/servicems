<template>
    <div class="flex justify-around w-full  mt-4 h-15 border-2 rounded-2xl">
        <!-- <h5 class="text-center mb-0 mt-0 font-bold">Date Filters</h5> -->
        <div class="flex items-center mx-24">
            <div class="flex-initial w-112">
                <DatePicker
                    v-model="filters['from_date']"
                    variant="outline"
                    placeholder="Select From Date"
                    label="From Date"
                />
            </div>
            <div class="flex-initial w-112">
                <DatePicker
                    v-model="filters['to_date']"
                    variant="outline"
                    placeholder="Select To Date"
                    label="To Date"
                />
            </div>
            <div class="flex-initial w-64">
                <Link
                    class="form-control"
                    :value="filters['workshop']"
                    doctype="Service Workshop"
                    placeholder="Service Workshop"
                    @change="(v) => (filters['workshop'] = v)"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Link from '../components/controls/Link.vue'

defineProps({
    filters: Object,
})

// watch (() => props.fromDate, (newVal) => {
//    = newVal
// })
</script>
