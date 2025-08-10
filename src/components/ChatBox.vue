<template>
  <div class="chat-container">
    <div class="chat-messages" ref="chatMessages">
      <div v-for="(msg, index) in messages" :key="index" class="chat-message">
        <strong>{{ msg.user }}:</strong> {{ msg.text }}
      </div>
      <div v-if="booting" class="chat-message"><em>Starting session…</em></div>
    </div>

    <div class="chat-input">
      <input
        v-model="newMessage"
        type="text"
        placeholder="Type a message..."
        @keyup.enter="sendMessage"
        :disabled="booting || sending"
      />
      <button @click="sendMessage" :disabled="booting || sending">
        {{ sending ? "Sending…" : "Send" }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  props: ["initialMessages", "personaName"], // pass personaName like "lincoln"
  data() {
    return {
      messages: this.initialMessages || [],
      newMessage: "",
      sessionId: null,
      booting: true,
      sending: false,
      BASE: import.meta?.env?.VITE_BACKEND_URL || "http://localhost:5000",
    };
  },
  async mounted() {
    await this.startSession();
  },
  methods: {
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatMessages;
        if (container) container.scrollTop = container.scrollHeight;
      });
    },
    async startSession() {
      try {
        const r = await fetch(`${this.BASE}/start_session/`, { method: "POST" });
        if (!r.ok) throw new Error(await r.text());
        const data = await r.json();
        this.sessionId = data.session_id;
      } catch (e) {
        console.error(e);
        this.messages.push({
          user: "System",
          text: "Could not start chat session. Check backend URL and try again.",
        });
      } finally {
        this.booting = false;
        this.scrollToBottom();
      }
    },
    async sendMessage() {
      const text = this.newMessage.trim();
      if (!text || this.booting || this.sending || !this.sessionId) return;

      // show user message immediately
      this.messages.push({ user: "You", text });
      this.newMessage = "";
      this.sending = true;
      this.scrollToBottom();

      try {
        const payload = {
          session_id: this.sessionId,
          user_message: text,
          persona_name: this.personaName || "lincoln", // default if not provided
        };

        const r = await fetch(`${this.BASE}/message/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!r.ok) {
          const errText = await r.text();
          throw new Error(errText);
        }

        const data = await r.json(); // { reply, model, session_id }
        this.messages.push({ user: "Bot", text: data.reply });
      } catch (e) {
        console.error(e);
        this.messages.push({
          user: "Bot",
          text: "Sorry, I couldn’t reach the model. Please try again.",
        });
      } finally {
        this.sending = false;
        this.scrollToBottom();
      }
    },
  },
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
