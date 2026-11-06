import { createApp } from 'vue'
import FieldApp from './FieldApp.vue'
import './style.css'

createApp(FieldApp).mount('#field-app')

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/field-sw.js', { scope: '/field' })
      .catch(() => {
        // A service worker is optional; online inspection remains functional.
      })
  })
}
