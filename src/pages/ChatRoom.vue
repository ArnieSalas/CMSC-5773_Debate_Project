<template>
  <div class="room-container">
    <h1 class="room-title">
      Chat Room
    </h1>
    <ChatBox :initial-messages="sampleMessages" />
  </div>
</template>

<script>
import ChatBox from "../components/ChatBox.vue";
import "../assets/styles.css";

export default {
  components: { ChatBox },
  data() {
    return {
      sampleMessages: [
        { user: "Charlie", text: "Hey everyone!" },
        { user: "Dana", text: "Hi Charlie!" }
      ]
    };
  }
};
</script>
