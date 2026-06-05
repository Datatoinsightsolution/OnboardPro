import { createApp } from 'vue'
import { Button, Input, FeatherIcon, Avatar, setConfig, frappeRequest } from 'frappe-ui'
import router from './router'
import App from './App.vue'
import './assets/risto.css'

const app = createApp(App)
setConfig('resourceFetcher', frappeRequest)
app.use(router)
;[Button, Input, FeatherIcon, Avatar].forEach((c) => app.component(c.name, c))
app.mount('#app')
