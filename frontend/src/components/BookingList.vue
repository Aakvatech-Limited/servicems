<template>
    <div class="scroll">
        <div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-6">
            <Card
                v-for="item in bay.data"
                :key="item.name"
                class="bg-white p-4 rounded-lg shadow-md"
            >
                <div class="mb-6">
                    <h5 class="font-bold text-sm mb-3">{{ item.name }}</h5>
                    <p class="text-sm text-gray-600">{{ item.service_workshop }}</p>
                </div>
                <div class="flex">
                    <Badge>{{ item.name }}</Badge>
                    <Button
                        class="flex-initial bg-blue-500 hover:bg-blue-600 text-white font-bold rounded"
                        label="View"
                        @click=""
                    />
                </div>
            </Card>
        </div>
        
        <div class="mt-6">
            <Button @click="bay.next()" class="bg-gray-800 hover:bg-gray-900 text-white font-bold py-2 px-4 rounded">Next Page</Button>
        </div>
    </div>
</template>



<script setup>
import { ref } from 'vue'
import { createResource, createListResource } from 'frappe-ui'

const bay = createListResource({
    doctype: 'Bay',
    fields: ['name', 'service_workshop'],
    auto: true,
    orderBy: 'name',
    start: 0,
    pageLength: 100,
})

bay.fetch()

</script>