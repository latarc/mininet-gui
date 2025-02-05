<template>
  <div class="webshell-container webshell" ref="webshell">
    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="(node, nodeId) in nodes"
        :key="nodeId"
        @click="setActiveTab(nodeId)"
        :class="{ active: activeTab === nodeId }"
      >
        {{ nodeId }}
      </button>
    </div>

    <!-- Terminal Window -->
    <div class="terminal-window" @click="focusInput">
      <pre ref="terminalOutput" class="terminal-output">
        {{ terminals[activeTab] }}<span :class="['cursor', isFocused ? 'filled' : 'empty']"></span>
      </pre>
      <input
        ref="inputField"
        v-model="userInputs[activeTab]"
        @keydown.prevent="handleKeydown"
        @focus="isFocused = true"
        @blur="isFocused = false"
        class="hidden-input"
        tabindex="-1"
      />
    </div>
  </div>
</template>

<script>
export default {
  props: ["nodes"],
  data() {
    return {
      terminals: {},
      sockets: {},
      userInputs: {},
      activeTab: null,
      isFocused: false,
    };
  },
  beforeUnmount() {
    Object.values(this.sockets).forEach(ws => ws?.close());
  },
  methods: {
    setActiveTab(nodeId) {
      this.activeTab = nodeId;
      this.focusInput();
      if (!this.sockets[nodeId]) this.initWebSocket(nodeId);
    },

    initWebSocket(nodeId) {
      if (this.sockets[nodeId]) return;
      
      const ws = new WebSocket(`ws://10.7.230.33:8000/api/mininet/terminal/${nodeId}`);
      
      ws.onopen = () => console.log(`Connected to ${nodeId}`);
      ws.onmessage = event => this.handleTerminalData(nodeId, event.data);
      ws.onerror = error => console.error(`WebSocket error (${nodeId}):`, error);
      ws.onclose = () => console.log(`WebSocket closed (${nodeId})`);
      
      this.sockets[nodeId] = ws;
    },

    handleTerminalData(nodeId, data) {
      if (data === "\b\u001b[K") {
        // Handle backspace by removing the last character
        this.terminals[nodeId] = this.terminals[nodeId].slice(0, -1);
      } else if (data === "\u0007") {
        // Ignore the bell character
        return;
      } else {
        this.terminals[nodeId] = (this.terminals[nodeId] || "") + data;
      }
      if (this.activeTab === nodeId) this.scrollToBottom();
    },

    sendChar(nodeId, char) {
      const ws = this.sockets[nodeId];
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(char);
      } else {
        console.log(`WebSocket for ${nodeId} is not connected. Reconnecting...`);
        this.initWebSocket(nodeId);
      }
    },

    handleKeydown(event) {
      const nodeId = this.activeTab;
      if (!nodeId) return;
      
      if (event.key === "Backspace") {
        this.sendChar(nodeId, "\b");
      } else if (event.key === "Enter") {
        this.sendChar(nodeId, "\n");
      } else if (event.key === "Tab") {
        this.sendChar(nodeId, "\t");
      } else {
        this.sendChar(nodeId, event.key);
      }
      this.scrollToBottom();
    },

    focusInput() {
      this.$refs.inputField?.focus();
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const webshell = this.$refs.webshell;
        if (webshell) {
          webshell.scrollTop = webshell.scrollHeight;
        }
      });
    }
  }
};
</script>

<style>
.hidden-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  margin-left: 2px;
  vertical-align: middle;
}

.filled {
  background-color: white;
}

.empty {
  border: 1px solid white;
}
</style>
