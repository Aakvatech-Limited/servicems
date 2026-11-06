<template>
  <div class="sm-record-link">
    <input
      :value="modelValue"
      :list="listId"
      :aria-label="label"
      :placeholder="placeholder || 'Search ' + doctype"
      :required="required"
      :disabled="disabled"
      class="sm-input"
      autocomplete="off"
      @focus="search(modelValue)"
      @input="input"
    />
    <datalist :id="listId">
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        {{ plainDescription(option.description) }}
      </option>
    </datalist>
    <small v-if="error" class="text-red-700" role="alert">{{ error }}</small>
  </div>
</template>
<script setup>
import { getCurrentInstance, onBeforeUnmount, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
const props = defineProps({
  modelValue: { type: String, default: '' },
  doctype: { type: String, required: true },
  label: String,
  placeholder: String,
  filters: { type: Object, default: () => ({}) },
  required: Boolean,
  disabled: Boolean,
})
const emit = defineEmits(['update:modelValue'])
const listId = 'calendar-link-' + getCurrentInstance().uid
const options = ref([])
const error = ref('')
let timer
let request = 0
const plainDescription = (value) => (value || '').replace(/<[^>]*>/g, ' ')
function input(event) {
  emit('update:modelValue', event.target.value)
  clearTimeout(timer)
  timer = setTimeout(() => search(event.target.value), 250)
}
async function search(text = '') {
  if (props.disabled) return
  const id = ++request
  error.value = ''
  try {
    const rows = await frappeRequest({
      url: 'frappe.desk.search.search_link',
      method: 'POST',
      params: {
        doctype: props.doctype,
        txt: text,
        filters: props.filters,
        page_length: 20,
      },
    })
    if (id === request) options.value = rows || []
  } catch (e) {
    if (id === request)
      error.value =
        e.messages?.join(' ') || e.message || 'Unable to search records.'
  }
}
watch(
  () => JSON.stringify(props.filters),
  () => {
    options.value = []
    request++
  }
)
onBeforeUnmount(() => {
  clearTimeout(timer)
  request++
})
</script>
<style scoped>
.sm-record-link {
  min-width: 0;
}
.sm-input {
  width: 100%;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #dce2ec;
  border-radius: 6px;
  background: white;
  font-size: 13px;
}
</style>
