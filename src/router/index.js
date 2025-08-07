import { createRouter, createWebHistory } from 'vue-router'
import ChatRoom from '../pages/ChatRoom.vue'
import DebateRoom from '../pages/DebateRoom.vue'

const routes = [
  { path: '/', component: ChatRoom },
  { path: '/chat', component: ChatRoom },
  { path: '/debate', component: DebateRoom }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
