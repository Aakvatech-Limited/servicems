<template>
    <div class="flex justify-around w-full  mt-4 h-15 border-2 rounded-2xl">
        <div class="flex items-center mx-24 gap-24">
            <div class="flex-initial w-64 border-2 border-cyan-500/50 shadow-cyan-900/50 rounded-2xl">
                <DatePicker
                    v-model="filters['from_date']"
                    variant="outline"
                    placeholder="Select From Date"
                />
            </div>
            <div class="flex-initial w-64 border-2 border-cyan-500/50 shadow-cyan-900/50 rounded-2xl">
                <DatePicker
                    v-model="filters['to_date']"
                    variant="outline"
                    placeholder="Select To Date"
                />
            </div>
            <div class="flex-initial w-64 border-2 border-cyan-500/50 shadow-cyan-900/50 rounded-2xl">
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
import Link from '../components/controls/Link.vue'

defineProps({
    filters: Object,
})
</script>
