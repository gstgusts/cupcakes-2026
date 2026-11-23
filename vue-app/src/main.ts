import { createApp } from 'vue'
import './index.css'
import App from './App.vue'
import { initKeycloak } from './keycloak.ts'

// Log in before Vue starts: the whole app needs a login, and keycloak.init() may run only once
initKeycloak().then(() => {
  createApp(App).mount('#app')
})
