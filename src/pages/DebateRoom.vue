
<template>
  <div class="page-container">
    <h1 class="title">
      {{ currentPage === 'debate' ? 'Debate Room' : 'Chat Room' }}
    </h1>

    <!-- Page Switch Tabs -->
    <div class="tabs">
      <button
        :class="{ active: currentPage === 'debate' }"
        @click="changePage('debate')"
      >
        Debate Room
      </button>
      <button
        :class="{ active: currentPage === 'chat' }"
        @click="changePage('chat')"
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
                :class="historical_figures.some(f => f.id === msg.sender) ? 'bot' : 'user'"
              >
                <div class="avatar">
                  <img
                    v-if="msg.sender === 'Genghis Khan'"
                    src="@/assets/avatars/genghis_avatar.png"
                  >
                  <img
                    v-else-if="msg.sender === 'Kim Jong Un'"
                    src="@/assets/avatars/kim_avatar.png"
                  >
                  <img
                    v-else-if="msg.sender === 'George Washington'"
                    src="@/assets/avatars/george_avatar.png"
                  >
                  <img
                    v-else-if="msg.sender === 'Donald Trump'"
                    src="@/assets/avatars/don_avatar.png"
                  >
                  <img
                    v-else
                    src="@/assets/avatars/user_avatar.png"
                  >
                </div>
                <div class="bubble">
                  <div class="name">
                    {{ msg.sender }}
                  </div>
                  <div class="text">
                    {{ msg.text }}
                  </div>
                </div>
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
              @click="toggleButton(key)"
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
      messages: [],
      historical_figures: [
        { id: "Genghis Khan" },
        { id: "Kim Jong Un" }, 
        { id: "George Washington" },
        { id: "Donald Trump" }
      ],
      newMessage: "",
      sessionId: null,
      toggles: {
        gk: { label: "Genghis Khan", state: false },
        kj: { label: "Kim Jong Un", state: false },
        gw: { label: "George Washington", state: false },
        dt: { label: "Donald Trump", state: false }
      },
      maxLength: 0,
      rebuttles: 0,
      lastBotReplied: null // Track who last replied
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
            persona_name: personaName.toLowerCase().replace(/ /g, "_"),
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
      let rebut = this.rebuttles
      if (!text) return;

      // Push user message
      this.messages.push({ sender: "You", text });
      this.newMessage = "";

      // Get active personas
      const active = Object.values(this.toggles)
        .filter(val => val.state)
        .map(val => val.label);

      // If no bots are selected, exit
      if (active.length === 0) {
        alert("Please select at least one persona.");
        return;
      }

      let currentMessage = text;
      let botResponses = [];

      for (let i = 0; i < rebut; i++) {
        try {
      const nextBot = active[(this.lastBotReplied ? active.indexOf(this.lastBotReplied) + 1 : 0) % active.length];

      const botReply = await this.sendToPersona(currentMessage, nextBot);
      botResponses.push({ sender: nextBot, text: botReply });

      currentMessage = botReply;
      this.lastBotReplied = nextBot;

      await new Promise(resolve => setTimeout(resolve, 500)); // 500ms delay between bots

      this.lastBotReplied = nextBot;

    } catch (error) {
      console.error("Error during bot response cycle:", error);
      break;
    }
      }

      this.messages.push(...botResponses);

      ++rebut;
    },
    stopDebate() {
      alert("Debate stopped.");
    },
    toggleButton(key) {
      if (this.currentPage === 'chat') {
        Object.keys(this.toggles).forEach(k => {
          this.toggles[k].state = false;
        });
        this.toggles[key].state = true;
      } else {
        this.toggles[key].state = !this.toggles[key].state;
      }
    },
    changePage(page) {
      this.currentPage = page;
      this.resetToggles();
    },
    resetToggles() {
      Object.keys(this.toggles).forEach(key => {
        this.toggles[key].state = false;
      });
    }
  }
};
</script>


<style scoped>
.page-container {
  max-width: 700px;
  background-image: url("../assets/chat_background.jpg");
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
  border: 1px solid #cccccc;
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
  border: 1px solid #cccccc;
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
.scroll-box {
  height: 300px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 10px;
}

.message {
  display: flex;
  align-items: flex-end;
  margin-bottom: 10px;
}

.message.bot {
  flex-direction: row;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.bubble {
  max-width: 60%;
  padding: 8px 12px;
  border-radius: 10px;
  margin: 0 8px;
}

.bot .bubble {
  background-color: #e5e5ea;
  color: #000;
}

.user .bubble {
  background-color: #1e90ff;
  color: #fff;
}

.name {
  font-weight: bold;
  font-size: 0.85em;
  margin-bottom: 3px;
}

.text {
  font-size: 1em;
}

.time {
  font-size: 0.75em;
  opacity: 0.7;
  margin-top: 4px;
  text-align: right;
}

</style>
