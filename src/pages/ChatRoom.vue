<template>
  <div class="p-4">
    <div class="flex space-x-4 mb-4">
      <button @click="activeTab = 'chat'" :class="tabClass('chat')">Chat</button>
      <button @click="activeTab = 'debate'" :class="tabClass('debate')">Debate</button>
    </div>

    <MessageBox :messages="messages" />

    <ChatControls :models="models" />

    <div class="mt-4">
      <label>Max Length:</label>
      <input type="number" v-model="maxLength" class="ml-2 border px-2 py-1" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MessageBox from '../components/MessageBox.vue'
import ChatControls from '../components/ChatControls.vue'

const activeTab = ref('chat')
const messages = ref(['Hello Chat!'])
const maxLength = ref(100)

const models = ref([
  { name: 'GV', selected: false, mult: 1 },
  { name: 'KJ', selected: false, mult: 1 },
  { name: 'DT', selected: false, mult: 1 },
  { name: 'GK', selected: false, mult: 1 }
])

const tabClass = (tab) =>
  activeTab.value === tab
    ? 'bg-green-600 text-white px-4 py-2 rounded'
    : 'bg-gray-200 text-black px-4 py-2 rounded'
</script>
