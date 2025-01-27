<template>
  <div class="webshell-container">
    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="(node, nodeId) in nodes"
        :key="nodeId"
        @click="activeTab = nodeId"
        :class="{ active: activeTab === nodeId }"
      >
        {{ nodeId }}
      </button>
    </div>

    <!-- Terminal Window -->
    <div class="terminal-window" v-if="activeTab" @click.prevent="focusInput">
      <!-- Terminal output -->
      <pre 
        @click.prevent="focusInput" 
        class="terminal-output"
      >
      {{ terminals[activeTab] }}
      </pre>
      
      <!-- Invisible input field -->
      <input
        ref="inputField"
        v-model="userInputs[activeTab]"
        @input="sendCommand(activeTab)"
        @keydown.enter.prevent="handleEnter"
        @keydown.tab.prevent="handleTab"
        @keydown.backspace.prevent="handleBackspace"
        autofocus
        class="hidden-input"
      />
    </div>
  </div>
</template>

<script>
export default {
  props: ["nodes"], // nodes is an object { h1: {...}, h2: {...} }
  data() {
    return {
      terminals: {},
      sockets: {},
      userInputs: {},
      activeTab: null,
    };
  },
  mounted() {
    if (!this.nodes || Object.keys(this.nodes).length === 0) return;

    Object.keys(this.nodes).forEach((nodeId) => {
      const ws = new WebSocket(`ws://10.7.230.33:8000/api/mininet/terminal/${nodeId}`);

      ws.onopen = () => {
        console.log(`WebSocket opened for ${nodeId}`);
        this.terminals[nodeId] = `Connected to ${nodeId}\n`;
      };

      ws.onmessage = (event) => {
        this.terminals[nodeId] += `${event.data}`;
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error for ${nodeId}:`, error);
      };

      ws.onclose = () => {
        console.log(`WebSocket closed for ${nodeId}`);
      };

      this.sockets[nodeId] = ws;
      this.terminals[nodeId] = "";
      this.userInputs[nodeId] = "";
    });

    this.activeTab = Object.keys(this.nodes)[0] || null;
  },
  beforeUnmount() {
    Object.values(this.sockets).forEach((ws) => ws.close());
  },
  methods: {
    sendCommand(nodeId) {
      if (!this.userInputs[nodeId]) return;

      const command = this.userInputs[nodeId];
      this.userInputs[nodeId] = ""; // Clear the input field

      if (!this.sockets[nodeId] || this.sockets[nodeId].readyState !== WebSocket.OPEN) {
        console.log(`WebSocket for ${nodeId} is not connected. Attempting to reconnect...`);

        this.sockets[nodeId] = new WebSocket(`ws://10.7.230.33:8000/api/mininet/terminal/${nodeId}`);

        this.sockets[nodeId].onopen = () => {
          console.log(`WebSocket reconnected for ${nodeId}`);
          this.sockets[nodeId].send(command);
        };

        this.sockets[nodeId].onmessage = (event) => {
          this.terminals[nodeId] += `${event.data}`;
        };

        this.sockets[nodeId].onerror = (error) => {
          console.error(`WebSocket error for ${nodeId}:`, error);
        };

        this.sockets[nodeId].onclose = () => {
          console.log(`WebSocket closed for ${nodeId}`);
        };

        return;
      }
      this.sockets[nodeId].send(command);
    },
    handleEnter() {
      const nodeId = this.activeTab;
      this.sockets[nodeId].send("\n");
      this.userInputs[nodeId] = "";
    },
    handleTab() {
      const nodeId = this.activeTab;
      this.sockets[nodeId].send("\t");
    },
    handleBackspace() {
      const nodeId = this.activeTab;
      const command = this.userInputs[nodeId];
      this.sockets[nodeId].send('\b \b');
    },
    focusInput() {
      // Focus the hidden input when terminal output is clicked
      console.log("FOCUS INPUT")
      this.$refs.inputField.focus();
    }
  }
};
</script>

<style scoped>
* {
  padding: 0;
  margin: 0;
}

/* Main Container */
.webshell-container {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 300px;
  background-color: black;
  color: white;
  display: flex;
  flex-direction: column;
  border-top: 2px solid #444;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid #666;
  padding: 5px;
  height: 40px;
}
.tabs button {
  background: none;
  border: none;
  color: white;
  padding: 8px 12px;
  cursor: pointer;
  font-weight: bold;
}
.tabs button.active {
  background: #222;
  border-bottom: 2px solid #00ff00;
}

/* Terminal Window */
.terminal-window {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
  height: 200px;
  width: 100%;
  font-family: monospace;
  white-space: pre-wrap;
  overflow-y: auto;
  position: relative;
}

/* Terminal Output */
.terminal-output {
  flex-grow: 1;
  height: 90%;
  width: 90%;
  color: #0f0;
  overflow-y: scroll;
  overflow-x: hidden; 
  word-wrap: break-word;
  cursor: text;
}

/* Terminal Input */
.hidden-input {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 0%;
  width: 0%;
  /* background: transparent; */
  border: none;
  outline: none;
  color: white;
  font-size: 16px;
  font-family: monospace;
  z-index: 1;
  /* visibility: hidden; Completely hide the input */
}
</style>
