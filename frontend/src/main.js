import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import Toast from 'vue-toastification';
import 'vue-toastification/dist/index.css';


import {
  Button,
  Card,
  Input,
  setConfig,
  frappeRequest,
  resourcesPlugin,
  DatePicker,
  Badge,
  Select,
  Dialog,
  FormControl,
  FeatherIcon
} from 'frappe-ui'

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)

app.use(router)
app.use(resourcesPlugin)
app.use(Toast, {
  position: "bottom-right",
  timeout: 6000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: true,
  hideProgressBar: true,
  closeButton: "button",
  icon: true,
  rtl: false
})

app.component('Button', Button)
app.component('Card', Card)
app.component('Input', Input)
app.component('DatePicker', DatePicker)
app.component('Badge', Badge)
app.component('Select', Select)
app.component('Dialog', Dialog)
app.component('FormControl', FormControl)
app.component('FeatherIcon', FeatherIcon)

app.mount('#app')
