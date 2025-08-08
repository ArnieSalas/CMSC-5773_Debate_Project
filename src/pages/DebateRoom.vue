
<template>
  <div class="page-container">
    <h1 class="title">
      {{ currentPage === 'debate' ? 'Debate Room' : 'Chat Room' }}
    </h1>

    <!-- Page Switch Tabs -->
    <div class="tabs">
      <button
        :class="{ active: currentPage === 'debate' }"
        @click="currentPage = 'debate'"
      >
        Debate Room
      </button>
      <button
        :class="{ active: currentPage === 'chat' }"
        @click="currentPage = 'chat'"
      >
        Chat Room
      </button>
    </div>

    <transition
      name="fade-slide"
      mode="out-in"
    >
      <div :key="currentPage">
        <transition
          name="fade-scale"
          mode="out-in"
        >
          <div :key="activeTab">
            <div
              ref="scrollBox"
              class="scroll-box"
            >
              <div
                v-for="(msg, index) in messages"
                :key="index"
                class="message"
              >
                {{ msg }}
              </div>
            </div>
          </div>
        </transition>

        <!-- Message Input -->
        <div class="message-input">
          <input
            v-model="newMessage"
            type="text"
            placeholder="Type a message..."
            @keyup.enter="sendMessage"
          >
          <button @click="sendMessage">
            Send
          </button>
        </div>

        <!-- Toggle Buttons -->
        <div class="controls">
          <div
            v-for="(option, key) in toggles"
            :key="key"
            class="toggle"
          >
            <span>{{ option.label }}</span>
            <button
              :class="{ on: option.state }"
              @click="option.state = !option.state"
            >
              {{ option.state ? 'ON' : 'OFF' }}
            </button>
          </div>
        </div>

        <!-- Settings -->
        <div class="settings">
          <label>
            Max Length:
            <input
              v-model="maxLength"
              type="number"
            >
          </label>

          <label v-if="currentPage === 'debate'">
            # Rebuttles:
            <input
              v-model="rebuttles"
              type="number"
            >
          </label>
        </div>

        <!-- Stop button -->
        <button
          v-if="currentPage === 'debate'"
          class="stop-btn"
          @click="stopDebate"
        >
          STOP
        </button>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  data() {
    return {
      currentPage: "debate",
      activeTab: "debate",
      messages: [
        "User1: Hello",
        "User2: Welcome",
        "User1: Let's debate this topic..."
      ],
      newMessage: "",
      sessionId: null,
      toggles: {
        gk: { label: "Genghis Khan", state: false },
        ks: { label: "Kim Jong Un", state: false },
        dt: { label: "George Washington", state: false },
        gv: { label: "Donald Trump", state: false }
      },
      maxLength: 0,
      rebuttles: 0
    };
  },
  async mounted() {
    this.scrollToBottom();
    await this.startSession();
  },
  updated() {
    this.scrollToBottom();
  },
  methods: {
    scrollToBottom() {
      this.$nextTick(() => {
        const box = this.$refs.scrollBox;
        if (box) {
          box.scrollTo({
            top: box.scrollHeight,
            behavior: "smooth"
          });
        }
      });
    },
    async startSession() {
      try {
        const res = await fetch("http://127.0.0.1:5000/start_session/", {
          method: "POST"
        });
        const data = await res.json();
        this.sessionId = data.session_id;
      } catch (error) {
        console.error("Failed to start session:", error);
      }
    },
    async sendToPersona(userMessage, personaName) {
      try {
        const res = await fetch("http://127.0.0.1:5000/message/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            session_id: this.sessionId,
            user_message: userMessage,
            persona_name: personaName.toLowerCase().replace(/ /g, "_")
          })
        });
        const data = await res.json();
        return data.reply;
      } catch (error) {
        console.error(`Error with ${personaName}:`, error);
        return "(No response)";
      }
    },
    async sendMessage() {
      const text = this.newMessage.trim();
      if (!text) return;

      this.messages.push(`User: ${text}`);
      this.newMessage = "";

      const active = Object.values(this.toggles)
        .filter(val => val.state)
        .map(val => val.label);

      for (const persona of active) {
        const reply = await this.sendToPersona(text, persona);
        this.messages.push(`${persona}: ${reply}`);
      }
    },
    stopDebate() {
      alert("Debate stopped.");
    }
  }
};
</script>

<style scoped>
.page-container {
  max-width: 700px;
  margin: auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}
.title {
  text-align: center;
  margin-bottom: 15px;
}
.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}
.tabs button {
  flex: 1;
  padding: 10px;
  cursor: pointer;
  background: #ddd;
  border: none;
  font-weight: bold;
  transition: background 0.2s;
}
.tabs button:hover {
  background: #bbb;
}
.tabs .active {
  background: #4caf50;
  color: white;
}
.scroll-box {
  height: 300px;
  overflow-y: auto;
  background: #f8f8f8;
  border: 1px solid #ccc;
  padding: 10px;
}
.message {
  margin: 5px 0;
}
.message-input {
  display: flex;
  margin-top: 8px;
}
.message-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ccc;
  border-right: none;
  outline: none;
}
.message-input button {
  background: #4caf50;
  color: white;
  border: none;
  padding: 8px 12px;
  cursor: pointer;
}
.message-input button:hover {
  background: #45a049;
}
.controls {
  display: flex;
  justify-content: space-around;
  margin: 15px 0;
}
.toggle {
  text-align: center;
}
.toggle button {
  display: block;
  padding: 5px 10px;
  margin-top: 5px;
  background: #bbb;
  border: none;
  cursor: pointer;
  border-radius: 4px;
}
.toggle button.on {
  background: #4caf50;
  color: white;
}
.settings {
  display: flex;
  justify-content: space-around;
  margin: 15px 0;
}
.settings label {
  display: flex;
  align-items: center;
}
.settings input {
  width: 60px;
  margin-left: 5px;
}
.stop-btn {
  display: block;
  margin: 20px auto;
  padding: 10px 20px;
  background: red;
  color: white;
  font-weight: bold;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}
.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
