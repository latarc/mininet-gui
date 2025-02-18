<template>
  <div class="webshell-container webshell" ref="webshell">
    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="node in nodes.get()"
        :key="node.id"
        @click="setActiveTab(node.id)"
        :class="{ active: activeTab === node.id }"
      >
        {{ node.id }}
      </button>
    </div>

    <!-- Terminal Window -->
    <div ref="terminalWindow" class="terminal-window" @click="focusInput">
      <pre ref="terminalOutput" class="terminal-output">
        {{ sanitizedTerminals[activeTab] }}<span :class="['cursor', isFocused ? 'filled' : 'empty']"></span>
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
      sanitizedTerminals: {},
      sockets: {},
      userInputs: {},
      activeTab: null,
      isFocused: false,
    };
  },
  watch: {
    nodes: {
      handler(newNodes) {
        if (newNodes.length === 0) {
          this.clearTerminals();
        }
      },
      deep: true,
    },
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
        this.terminals[nodeId] = this.terminals[nodeId].slice(0, -1);
      } else if (data === "\u0007") {
        return;
      } else if (data.includes("[H\u001b[2J\u001b[3J\u001b")) {
        this.terminals[nodeId] = ""; // Clear the terminal but do not delete history
      } else {
        this.terminals[nodeId] = (this.terminals[nodeId] || "") + data;
      }
      
      // Sanitize output
      this.sanitizedTerminals[nodeId] = this.terminals[nodeId]
        .replace(/\[\?2004[lh]/g, "")
        .replace(/\u001b\r\u001b/g, "")
        .replace(/\u001b/g, ""); // Remove standalone escape characters
      
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
        const terminalOutput = this.$refs.terminalOutput;
        if (terminalOutput) {
          terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
      });
    },

    clearTerminals() {
      Object.values(this.sockets).forEach(ws => ws?.close());
      this.terminals = {};
      this.sanitizedTerminals = {};
      this.userInputs = {};
      this.sockets = {};
      this.activeTab = null;
    }
  }
};
</script>

<style>
.hidden-input {
  position: fixed;
  opacity: 0;
  pointer-events: none;
}

.terminal-window {
  margin-left: 2%;
  width: 98%;
  height: 80%;
}

.terminal-output {
  width: 100%;
  height: 100%;
  overflow-y: scroll;
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
