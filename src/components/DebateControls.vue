<template>
  <div class="grid grid-cols-4 gap-2">
    <div v-for="model in models" :key="model.name">
      <label>{{ model.name }}</label>
      <input type="checkbox" v-model="model.selected" />
      <input type="number" v-model.number="model.mult" placeholder="Mult" class="w-full mt-1 border px-1" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  models: Array
})
</script>
