<template>
  <span class="field-icon" aria-hidden="true" v-html="svg"></span>
</template>
<script setup>
import { computed } from 'vue'
import icon0 from 'feather-icons/dist/icons/alert-circle.svg?raw'
import icon1 from 'feather-icons/dist/icons/arrow-left.svg?raw'
import icon2 from 'feather-icons/dist/icons/arrow-right.svg?raw'
import icon3 from 'feather-icons/dist/icons/briefcase.svg?raw'
import icon4 from 'feather-icons/dist/icons/camera.svg?raw'
import icon5 from 'feather-icons/dist/icons/check.svg?raw'
import icon6 from 'feather-icons/dist/icons/check-circle.svg?raw'
import icon7 from 'feather-icons/dist/icons/check-square.svg?raw'
import icon8 from 'feather-icons/dist/icons/chevron-right.svg?raw'
import icon9 from 'feather-icons/dist/icons/chevron-up.svg?raw'
import icon10 from 'feather-icons/dist/icons/chevron-down.svg?raw'
import icon11 from 'feather-icons/dist/icons/clipboard.svg?raw'
import icon12 from 'feather-icons/dist/icons/clock.svg?raw'
import icon13 from 'feather-icons/dist/icons/edit-3.svg?raw'
import icon14 from 'feather-icons/dist/icons/external-link.svg?raw'
import icon15 from 'feather-icons/dist/icons/eye.svg?raw'
import icon16 from 'feather-icons/dist/icons/grid.svg?raw'
import icon17 from 'feather-icons/dist/icons/image.svg?raw'
import icon18 from 'feather-icons/dist/icons/log-in.svg?raw'
import icon19 from 'feather-icons/dist/icons/log-out.svg?raw'
import icon20 from 'feather-icons/dist/icons/map-pin.svg?raw'
import icon21 from 'feather-icons/dist/icons/maximize-2.svg?raw'
import icon22 from 'feather-icons/dist/icons/moon.svg?raw'
import icon23 from 'feather-icons/dist/icons/navigation.svg?raw'
import icon24 from 'feather-icons/dist/icons/plus.svg?raw'
import icon25 from 'feather-icons/dist/icons/refresh-cw.svg?raw'
import icon26 from 'feather-icons/dist/icons/save.svg?raw'
import icon27 from 'feather-icons/dist/icons/search.svg?raw'
import icon28 from 'feather-icons/dist/icons/shield.svg?raw'
import icon29 from 'feather-icons/dist/icons/sun.svg?raw'
import icon30 from 'feather-icons/dist/icons/truck.svg?raw'
import icon31 from 'feather-icons/dist/icons/user.svg?raw'
import icon32 from 'feather-icons/dist/icons/x.svg?raw'
const icons = {
  'alert-circle': icon0,
  'arrow-left': icon1,
  'arrow-right': icon2,
  briefcase: icon3,
  camera: icon4,
  check: icon5,
  'check-circle': icon6,
  'check-square': icon7,
  'chevron-right': icon8,
  'chevron-up': icon9,
  'chevron-down': icon10,
  clipboard: icon11,
  clock: icon12,
  'edit-3': icon13,
  'external-link': icon14,
  eye: icon15,
  grid: icon16,
  image: icon17,
  'log-in': icon18,
  'log-out': icon19,
  'map-pin': icon20,
  'maximize-2': icon21,
  moon: icon22,
  navigation: icon23,
  plus: icon24,
  'refresh-cw': icon25,
  save: icon26,
  search: icon27,
  shield: icon28,
  sun: icon29,
  truck: icon30,
  user: icon31,
  x: icon32,
}
const props = defineProps({ name: { type: String, required: true } })
const svg = computed(() => icons[props.name] || '')
</script>
