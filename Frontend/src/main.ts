import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

import { createPinia } from 'pinia'
import router from './router'


// Fix: иконки по умолчанию
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl

L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})


const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

