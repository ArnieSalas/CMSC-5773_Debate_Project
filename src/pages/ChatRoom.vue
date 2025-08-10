<template>
  <div class="room-container">
    <h1 class="room-title">Chat Room</h1>
    <ChatBox
      v-if="sessionId"
      :session-id="sessionId"
      persona-name="lincoln"   <!-- change to your persona filename -->
    />
    <div v-else class="text-sm opacity-70">Starting session…</div>
  </div>
</template>

<script>
import ChatBox from "../components/ChatBox.vue";
import "../assets/styles.css";
import { sendMessage } from "../api/llm";

export default {
  components: { ChatBox },
  data() {
    return { sessionId: null };
  },
  async mounted() {
    try {
      this.sessionId = await sendMessage();
    } catch (e) {
      console.error(e);
      alert("Could not start chat session.");
    }
  },
};
</script>
