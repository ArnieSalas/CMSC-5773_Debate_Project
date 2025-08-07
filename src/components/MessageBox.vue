<template>
  <div class="border h-64 overflow-y-scroll p-2 bg-white shadow">
    <div v-for="(msg, idx) in messages" :key="idx" class="mb-1">
      {{ msg }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  messages: Array
})
</script>
