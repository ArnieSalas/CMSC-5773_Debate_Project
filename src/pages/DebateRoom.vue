
<template style="background">
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
                    v-else-if="msg.sender === 'Albert Einstein'"
                    src="@/assets/avatars/albert_einstein_avatar.png"
                  >
                  <img
                    v-else-if="msg.sender === 'Joan of Arc'"
                    src="@/assets/avatars/joan_of_arc_avatar.png"
                  >
                  <img
                    v-else-if="msg.sender === 'Mahatma Gandhi'"
                    src="@/assets/avatars/mahatma_gandhi_avatar.png"
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
          <button :disabled="isDisabled" @click="handleMessageSend">
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
          <label v-if="currentPage === 'debate'">
            Total Number of Responses:
            <!-- Slider for Rebuttles with increased size -->
            <input
              v-model="rebuttles"
              type="range"
              min="0"
              max="20"
              step="1"
              @input="updateRebuttlesDisplay"
              class="rebuttles-slider"
            >
            <!-- Display the current value of the slider -->
            <span>{{ rebuttles }}</span>
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
        { id: "Donald Trump" },
        { id: "Albert Einstein" },
        { id: "Joan of Arc" },
        { id: "Mahatma Gandhi" }
      ],
      newMessage: "",
      sessionId: null,
      toggles: {
        gk: { label: "Genghis Khan", state: false },
        kj: { label: "Kim Jong Un", state: false },
        gw: { label: "George Washington", state: false },
        dt: { label: "Donald Trump", state: false },
        ae: { label: "Albert Einstein", state: false },
        ja: { label: "Joan of Arc", state: false },
        mg: { label: "Mahatma Gandhi", state: false }
      },
      maxLength: 0,
      rebuttles: 0,
      isDisabled: false,
      lastBotReplied: null, // Track who last replied
      shouldStop: false
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
    handleMessageSend() {
      if (this.currentPage === "debate") {
        this.sendMessage();
      }
      else if (this.currentPage === "chat") {
        this.sendChatMessage();
      }
    },
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
    updateRebuttlesDisplay() {
      // Optionally update any other properties or perform actions on input change
      console.log(`Rebuttles set to: ${this.rebuttles}`);
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
    async sendChatMessage() {
      this.shouldStop = false;
      const text = this.newMessage.trim();
      if (!text) return;

      // Push user message
      this.messages.push({ sender: "You", text});
      this.newMessage = "";

      const active = Object.values(this.toggles)
        .filter(val => val.state)
        .map(val => val.label);

      for (const persona of active) {
        const reply = await this.sendToPersona(text, persona);
        this.messages.push({ sender: persona, text: reply});
      }
    },
    async sendMessage() {
      this.shouldStop = false;
      const text = this.newMessage.trim();
      let rebut = this.rebuttles
      this.isDisabled = true;
      if (!text) return;

      this.messages.push({ sender: "You", text });
      this.newMessage = "";

      const active = Object.values(this.toggles)
        .filter(val => val.state)
        .map(val => val.label);

      if (active.length === 0) {
        alert("Please select at least one persona.");
        this.isDisabled = false;
        return;
      }

      let currentMessage = text;

      for (let i = 0; i < rebut; i++) {
        try {
          
          if(this.shouldStop == true) {
            break;
          }
      const nextBot = active[(this.lastBotReplied ? active.indexOf(this.lastBotReplied) + 1 : 0) % active.length];

      const botReply = await this.sendToPersona(currentMessage, nextBot);
      this.messages.push({ sender: nextBot, text: botReply });

      currentMessage = botReply;
      this.lastBotReplied = nextBot;

      await new Promise(resolve => setTimeout(resolve, 500));

      this.lastBotReplied = nextBot;

    } catch (error) {
      console.error("Error during bot response cycle:", error);
      this.isDisabled = false;
      break;
    }
      }
      this.isDisabled = false;
    },
    stopDebate() {
      alert("Debate stopped.");
      this.shouldStop = true;
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
      this.shouldStop = true;
      this.currentPage = page;
      this.resetToggles();
      this.messages.length = 0;
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
:global(html, body, #app) {
  height: 100%;
  margin: 0;
}

:global(body) {
  background-image: url("../assets/chat_background.jpg");
  background-size: cover;      /* Fill the viewport */
  background-position: center; /* Keep it centered */
  background-repeat: no-repeat;
  background-attachment: fixed; /* Optional: nice parallax when scrolling */
}
 .page-container {
  width: min(980px, 100% - 32px);
  margin: 32px auto;
  padding: 20px;
}
.app-card {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  background: var(--bg-card);
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: var(--radius);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.background{
  background-image: url("../assets/chat_background.jpg");
  background-size: cover;   /* fills screen, keeps aspect ratio */
  background-position: center;
  background-repeat: no-repeat;
  width: 100vw;
  height: 100vh;
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
  min-height: 20vh;
  max-height: 40vh;                         /* largest allowed */
  height: auto;
  overflow-y: auto;                       /* scroll once capped */
  background: #f8f8f8;
  border: 1px solid #cccccc;
  padding: 10px;
  border-radius: 90px;
  transition: max-height 0.2s ease;          /* smooth growth */
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
  display: flex;
  flex-direction: column; /* stack name above button */
  align-items: center;    /* center horizontally */
  gap: 0.25rem;           /* space between text and button */
}
.toggle button {
  display: block;
  padding: 5px 10px;
  margin-top: 5px;
  background: #bbb;
  border: none;
  cursor: pointer;
  border-radius: 4px;
  min-width: 50px;
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

.message {
  display: flex;
  align-items: flex-end;
  margin-bottom: 10px;
}

.message.bot {
  flex-direction: row;
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

/* changes input and send button, glows, ovals, etc */
.message-input {
  display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 12px 20px 20px;
}
.message-input input {
  padding: 12px 14px; border-radius: 999px; border: 1px solid #e4e4e4; outline: none;
  background: rgba(255,255,255,.9);
  transition: box-shadow .2s ease, border-color .2s ease;
}
.message-input input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(63,191,111,.15);
}
.message-input button {
  border: 0; padding: 12px 18px; border-radius: 999px; font-weight: 800; cursor: pointer;
  color: white; box-shadow: 0 8px 24px rgba(63,191,111,.35);
  transition: transform .12s ease, box-shadow .2s ease;
}
.message-input button:hover { transform: translateY(-1px); box-shadow: 0 10px 28px rgba(63,191,111,.45); }
.message-input button:active { transform: translateY(0); }


.message.user {
  flex-direction: row-reverse;
}
/* This chunk adds the user's profile coming up in a smooth way as well as makes the input prittier */
.message { display: flex; gap: 10px; margin: 8px 0; animation: pop .12s ease; }
/* .message.user .bubble { flex-direction: row-reverse; background: #fff; border: 1px solid #eee; } */
.message.bot .bubble  { background: #e9f9f0; border: 1px solid rgba(63,191,111,.25); }
.bubble {
  max-width: 72ch; padding: 10px 12px; border-radius: 14px;
  box-shadow: 0 4px 14px rgba(0,0,0,.05);
  position: relative;
}
.message.user .bubble::after, .message.bot .bubble::after {
  content: ""; position: absolute; bottom: -2px; width: 0; height: 0; border: 8px solid transparent;
}
/* .message.user .bubble::after { right: -2px; border-left-color: #eee; } */
.message.bot  .bubble::after { left:  -2px; border-right-color: rgba(63,191,111,.25); }
@keyframes pop { from { transform: translateY(4px); opacity: .0 } to { transform: none; opacity: 1 } }
.name { font-weight: 700; margin-bottom: 2px; color: var(--text) }
.text { color: var(--text); }
.time { color: var(--text-muted); font-size: 12px; margin-top: 4px; }


/* Room selection is rouned/ transitions better */
.tabs {
  display: grid; grid-template-columns: 1fr 1fr;
  background: rgba(0,0,0,.05); padding: 6px; border-radius: 999px; gap: 6px; margin: 16px 20px;
}
.tabs button {
  border: 0; padding: 10px 14px; border-radius: 999px; cursor: pointer;
  background: transparent; font-weight: 700; transition: transform .15s ease, background .2s ease;
}
.tabs button:active { transform: scale(.98); }

.toggle span {
  font-weight: 600;
  font-size: 1rem; /* tweak as needed */
  color: #fff;     /* white text on your parchment background */
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* improves readability */
}

.settings label {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 1rem;
  color: #fff;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.settings input {
  width: 60px;
  margin-left: 5px;
  border: none;
  padding: 4px;
  border-radius: 4px;
}

.title {
  font-family: 'Poppins', sans-serif; /* Clean modern font */
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(90deg, #464746, #434943);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
  letter-spacing: 2px;
  margin-bottom: 20px;
  text-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
  animation: fadeInDown 0.6s ease-out;
}

</style>
