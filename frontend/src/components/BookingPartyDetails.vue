<template>
  <section v-if="isNewCustomer" class="border-t pt-4">
    <h4 class="mb-4 font-semibold text-cyan-700">Customer Details</h4>
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      <div>
        <label
          for="booking-customer-name"
          class="mb-2 block text-sm font-semibold"
          >Customer Name *</label
        ><input
          id="booking-customer-name"
          v-model="newCustomer.customer_name"
          required
          class="form-input w-full"
        />
      </div>
      <div>
        <label
          for="booking-customer-type"
          class="mb-2 block text-sm font-semibold"
          >Customer Type *</label
        ><select
          id="booking-customer-type"
          v-model="newCustomer.customer_type"
          class="form-select w-full"
        >
          <option>Company</option>
          <option>Individual</option>
          <option>Partnership</option>
        </select>
      </div>
      <Link
        v-model="newCustomer.customer_group"
        doctype="Customer Group"
        label="Customer Group *"
        placeholder="Customer Group"
      />
      <Link
        v-model="newCustomer.territory"
        doctype="Territory"
        label="Territory *"
        placeholder="Territory"
      />
      <div>
        <label for="booking-tax-id" class="mb-2 block text-sm font-semibold"
          >TIN</label
        ><input
          id="booking-tax-id"
          v-model="newCustomer.tax_id"
          class="form-input w-full"
        />
      </div>
      <div>
        <label for="booking-mobile" class="mb-2 block text-sm font-semibold"
          >Mobile No</label
        ><input
          id="booking-mobile"
          v-model="newCustomer.mobile_no"
          class="form-input w-full"
        />
      </div>
    </div>
  </section>
  <section v-if="isNewVehicle" class="border-t pt-4">
    <h4 class="mb-4 font-semibold text-cyan-700">Vehicle Details</h4>
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      <div>
        <label
          for="booking-registration"
          class="mb-2 block text-sm font-semibold"
          >Registration Number *</label
        ><input
          id="booking-registration"
          v-model="newVehicle.registration_number"
          required
          class="form-input w-full"
        />
      </div>
      <div>
        <label for="booking-engine" class="mb-2 block text-sm font-semibold"
          >Engine Number</label
        ><input
          id="booking-engine"
          v-model="newVehicle.engine_number"
          class="form-input w-full"
        />
      </div>
      <div>
        <label for="booking-chassis" class="mb-2 block text-sm font-semibold"
          >Chassis Number</label
        ><input
          id="booking-chassis"
          v-model="newVehicle.chassis_number"
          class="form-input w-full"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import Link from './controls/Link.vue'

defineProps({
  isNewCustomer: Boolean,
  isNewVehicle: Boolean,
  newCustomer: Object,
  newVehicle: Object,
})
</script>
