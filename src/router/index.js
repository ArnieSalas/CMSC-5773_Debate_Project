import { createRouter, createWebHistory } from 'vue-router'
import DebateRoom from '../pages/DebateRoom.vue'

const routes = [
  { path: '/', component: DebateRoom},
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
