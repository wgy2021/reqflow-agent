import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(ElementPlus)
app.use(router)

for (const [iconName, iconComponent] of Object.entries(
  ElementPlusIconsVue,
)) {
  app.component(iconName, iconComponent)
}

app.mount('#app')