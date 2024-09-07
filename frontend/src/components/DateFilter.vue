<template>
    <Card class="w-full max-w-screen-lg mt-2">
        <h5 class="text-center mb-6 mt-0 font-bold">Date Filters</h5>
        <div class="flex p-2 space-x-16 mx-20">
            <div class="flex-initial w-96">
                <DatePicker
                    v-model="fromDate"
                    variant="outline"
                    placeholder="Select From Date"
                    :disabled="fromDisabled"
                    label="From Date"
                />
            </div>
            <div class="flex-initial w-96">
                <DatePicker
                    v-model="toDate"
                    variant="outline"
                    placeholder="Select To Date"
                    :disabled="toDisabled"
                    label="To Date"
                />
            </div>
        </div>
    </Card>
</template>

<script setup>
import { ref } from 'vue'
const fromDate = ref('')
const toDate = ref('')
const fromDisabled = ref(false)
const toDisabled = ref(false)
</script>
