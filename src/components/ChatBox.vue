<template>
  <div class="chat-container">
    <div class="chat-messages" ref="chatMessages">
      <div v-for="(msg, index) in messages" :key="index" class="chat-message">
        <strong>{{ msg.user }}:</strong> {{ msg.text }}
      </div>
    </div>

    <div class="chat-input">
      <input
        v-model="newMessage"
        type="text"
        placeholder="Type a message..."
        @keyup.enter="sendMessage"
      />
      <button @click="sendMessage">Send</button>
    </div>
  </div>
</template>

<script>
export default {
  props: ["initialMessages"],
  data() {
    return {
      messages: this.initialMessages || [],
      newMessage: ""
    };
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim()) {
        this.messages.push({ user: "You", text: this.newMessage });
        this.newMessage = "";
        this.scrollToBottom();
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatMessages;
        container.scrollTop = container.scrollHeight;
      });
    }
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #ccc;
  height: 400px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #f9f9f9;
}

.chat-message {
  padding: 6px 0;
  border-bottom: 1px solid #eee;
}

.chat-input {
  display: flex;
  border-top: 1px solid #ccc;
}

.chat-input input {
  flex: 1;
  padding: 10px;
  border: none;
  outline: none;
}

.chat-input button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0 15px;
  cursor: pointer;
}

.chat-input button:hover {
  background: #0056b3;
}
</style>
