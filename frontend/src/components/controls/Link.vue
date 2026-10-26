<template>
  <div class="space-y-1.5" v-if="!attrs.disabled">
    <label class="block" :class="labelClasses" v-if="attrs.label">
      {{ attrs.label }}
    </label>
    <Autocomplete
      ref="autocomplete"
      :options="options.data"
      v-model="value"
      :size="attrs.size || 'sm'"
      :variant="attrs.variant"
      :placeholder="attrs.placeholder"
      :filterable="false"
    >
      <template #target="{ open, togglePopover }">
        <slot name="target" v-bind="{ open, togglePopover }" />
      </template>

      <template #prefix>
        <slot name="prefix" />
      </template>

      <template #item-prefix="{ active, selected, option }">
        <slot name="item-prefix" v-bind="{ active, selected, option }" />
      </template>

      <template #item-label="{ active, selected, option }">
        <slot name="item-label" v-bind="{ active, selected, option }" />
      </template>

      <template #footer="{ value, close }">
        <div v-if="attrs.onCreate">
          <Button
            type="button"
            variant="ghost"
            class="w-full !justify-start"
            :label="Create"
            New
            @click="attrs.onCreate(value, close)"
          >
            <template #prefix>
              <FeatherIcon name="plus" class="h-4" />
            </template>
          </Button>
        </div>
        <div>
          <Button
            type="button"
            variant="ghost"
            class="w-full !justify-start"
            label="Clear"
            @click="() => clearValue(close)"
          >
            <template #prefix>
              <FeatherIcon name="x" class="h-4" />
            </template>
          </Button>
        </div>
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import Autocomplete from '../../components/controls/Autocomplete.vue'
import { watchDebounced } from '@vueuse/core'
import { createResource } from 'frappe-ui'
import { useToast } from '@/composables/useToast.js'
import { useAttrs, computed, ref, watch } from 'vue'

const props = defineProps({
  filters: { type: Object, default: () => ({}) },
  doctype: {
    type: String,
    required: true,
  },
  modelValue: {
    type: String,
    default: '',
  },
  hideMe: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const attrs = useAttrs()
const { handleResourceError } = useToast()

const valuePropPassed = computed(() => 'value' in attrs)

const value = computed({
  get: () => (valuePropPassed.value ? attrs.value : props.modelValue),
  set: (val) => {
    emit(
      valuePropPassed.value ? 'change' : 'update:modelValue',
      val?.value || '',
    )
  },
})

const autocomplete = ref(null)
const text = ref('')

watchDebounced(
  () => autocomplete.value?.query,
  (val) => {
    val = val || ''
    if (text.value === val) return
    text.value = val
    reload(val)
  },
  { debounce: 300, immediate: true },
)

watchDebounced(
  () => props.doctype,
  () => reload(''),
  { debounce: 300, immediate: true },
)

watch(
  () => props.filters,
  () => reload(text.value),
  { deep: true },
)

const options = createResource({
  url: 'servicems.api.api.search_link_data',
  method: 'GET',
  params: {
    txt: text.value,
    doctype: props.doctype,
    filters: JSON.stringify(props.filters),
  },
  transform: (data) => {
    let allData = data.map((option) => {
      return {
        label: option.value,
        value: option.value,
      }
    })
    if (!props.hideMe && props.doctype == 'User') {
      allData.unshift({
        label: '@me',
        value: '@me',
      })
    }
    return allData
  },
})

function reload(val) {
  if (
    options.data?.length &&
    val === options.params?.txt &&
    props.doctype === options.params?.doctype &&
    JSON.stringify(props.filters) === options.params?.filters
  )
    return

  options.update({
    params: {
      txt: val,
      doctype: props.doctype,
      filters: JSON.stringify(props.filters),
    },
  })
  options.reload().catch(handleResourceError)
}

function clearValue(close) {
  emit(valuePropPassed.value ? 'change' : 'update:modelValue', '')
  close()
}

const labelClasses = computed(() => {
  return [
    {
      sm: 'text-xs',
      md: 'text-base',
    }[attrs.size || 'sm'],
    'text-gray-600',
  ]
})
</script>
