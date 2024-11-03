<template>
  <div v-for="field in section.fields" :key="field.name">
    <div
      v-if="field.type != 'Check'"
      class="mb-2 text-base text-gray-900 font-semibold"
    >
      {{ field.label}}
      <span 
        class="text-red-500 text-xl"
        v-if="field.reqd && !((field.name === 'customer' && data['Service Booking']['is_new_customer']) || (field.name === 'service_vehicle' && data['Service Booking']['is_new_vehicle']))"
      >
        *
      </span>
    </div>
    <FormControl
      v-if="field.read_only && field.type !== 'Check'"
      type="text"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
      :disabled="true"
      variant="outline"
    />
    <FormControl
      v-else-if="field.type === 'Select'"
      type="select"
      class="form-control"
      :class="field.prefix ? 'prefix' : ''"
      :options="field.options"
      v-model="data[section.doctype][field.name]"
      :placeholder="field.placeholder || field.label"
      variant="outline"
    >
      <template v-if="field.prefix" #prefix>
        <IndicatorIcon :class="field.prefix" />
      </template>
    </FormControl>
    <div
      v-else-if="field.type == 'Check'"
      class="flex items-center gap-2"
    >
      <FormControl
        class="form-control"
        type="checkbox"
        v-model="data[section.doctype][field.name]"
        @change="(e) => updateCheckValue(section.doctype, field.name, e.target.checked)"
        :disabled="Boolean(field.read_only)"
        variant="outline"
      />
      <label
        class="text-sm text-gray-900 font-bold"
      >
        {{ field.label }}
        <span class="text-red-500 text-xl" v-if="field.reqd">*</span>
      </label>
    </div>
    <Link
      v-else-if="field.type === 'Link' "
      class="form-control"
      :value="data[section.doctype][field.name]"
      :doctype="field.options"
      @change="(v) => (data[section.doctype][field.name] = v)"
      :placeholder="field.placeholder || field.label"
      :onCreate="field.create"
      :disabled="(field.name === 'customer' && data['Service Booking']['is_new_customer']) || (field.name === 'service_vehicle' && data['Service Booking']['is_new_vehicle'])"
    />
    <DatePicker
      v-else-if="field.type === 'Date'"
      v-model="data[section.doctype][field.name]"
      :placeholder="field.placeholder || field.label"
    />
    <FormControl
      v-else-if="field.type === 'Time'"
      type="time"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
    />
    <FormControl
      v-else-if="
        ['Small Text', 'Text', 'Long Text'].includes(field.type)
      "
      type="textarea"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
      :value="data[section.doctype][field.name]"
      @input="(e) => updateField(section.doctype, field.name, e.target.value)"
    />
    <FormControl
      v-else-if="['Int'].includes(field.type)"
      type="number"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
      @input="(e) => updateField(section.doctype, field.name, e.target.value)"
    />
    <FormControl
      v-else
      type="text"
      :placeholder="field.placeholder || field.label"
      :value="data[section.doctype][field.name]"
      v-model="data[section.doctype][field.name]"
      @input="(e) => updateField(section.doctype, field.name, e.target.value)"
      :disabled="Boolean(field.read_only)"
    />
  </div>
</template>

<script setup>
import IndicatorIcon from '../components/icons/IndicatorIcon.vue';
import Link from '../components/controls/Link.vue';

const props = defineProps({
  section: Object,
  data: Object,
})

function updateField(doctype, name, value) {
  const data = props.data;
  if (data[doctype]) {  
    data[doctype][name] = value;
  }
}

function updateCheckValue(doctype, name, value) {
  const data = props.data;
  if (data[doctype]) {
    data[doctype][name] = value;
  }
  if (data['Service Booking']['is_new_customer']) {
    data['Service Booking']['customer'] = '';
  }
  if (data['Service Booking']['is_new_vehicle']) {
    data['Service Booking']['service_vehicle'] = '';
  }
}
</script>

<style scoped>
:deep(.form-control.prefix select) {
  padding-left: 2rem;
}
</style>
