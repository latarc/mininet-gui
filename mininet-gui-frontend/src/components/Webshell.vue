<template>
  <div class="webshell-container">
    <div class="webshell-header">
      <i class="mdi mdi-console"></i>
      <span class="title">WebShell</span>
    </div>

    <div class="tabs">
      <button
        v-for="node in nodes.get()"
        :key="node.id"
        @click="setActiveTab(node.id)"
        :class="{ active: activeTab === node.id }"
        class="tab-button"
      >
        {{ node.id }}
      </button>
    </div>

    <div class="terminal-window" @click="focusInput">
      <pre ref="terminalOutput" class="terminal-output">
        <!-- the cursor MUST be in the same line as the terminal text or else it breaks -->
        {{ sanitizedTerminals[activeTab] }}<span :class="['cursor', isFocused ? 'filled' : 'empty']"></span>
      </pre>
      <input
        ref="inputField"
        v-model="userInputs[activeTab]"
        @keydown.prevent="handleKeydown"
        @keyup="handleKeyup"
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
      ctrlPressed: false,
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
      const ws = new WebSocket(`ws://127.0.0.1:8000/api/mininet/terminal/${nodeId}`);
      
      ws.onopen = () => console.log(`Connected to ${nodeId}`);
      ws.onmessage = event => this.handleTerminalData(nodeId, event.data);
      ws.onerror = error => console.error(`WebSocket error (${nodeId}):`, error);
      ws.onclose = () => console.log(`WebSocket closed (${nodeId})`);
      
      this.sockets[nodeId] = ws;
    },

    handleTerminalData(nodeId, data) {
      if (!this.terminals[nodeId]) this.terminals[nodeId] = "";

      // backspace
      if (data === ("\b \b") || data === "\b\x1b[K") {
        this.terminals[nodeId] = this.terminals[nodeId].replace(/.$/, "");
        this.sanitizedTerminals[nodeId] = this.terminals[nodeId];
        return;
      }

      // Ignore "bell" char
      if (data === "\u0007") return;

      if (data.includes("[H\u001b[2J\u001b[3J\u001b")) {
        this.terminals[nodeId] = "";
        this.sanitizedTerminals[nodeId] = this.terminals[nodeId];
        return;
      }

      data = data.replace(/\x1b\]0;.*?\x07/g, "");
      data = data.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, "");
      data = data.replace(/\x1b\[\?2004[hl]/g, "");
      data = data.replace(/\u001b/g, "");

      this.terminals[nodeId] += data;
      this.sanitizedTerminals[nodeId] = this.terminals[nodeId];

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

      if (["Shift", "CapsLock", "Dead", "Alt"].includes(event.key)) {
        return;
      }

      if (event.key === "Control") {
        this.ctrlPressed = true;
        return;
      }

      // Ctrl + C
      if (this.ctrlPressed && event.key.toLowerCase() === "c") {
        this.sendChar(nodeId, "\x03");
      }
      // Ctrl + L
      else if (this.ctrlPressed && event.key.toLowerCase() === "l") {
        this.sendChar(nodeId, "\u001b[H\u001b[2J\u001b[3J\u001b");
      }
      else if (event.key === "Backspace") {
        this.sendChar(nodeId, "\b");
      }
      else if (event.key === "Enter") {
        this.sendChar(nodeId, "\n");
      }
      else if (event.key === "Tab") {
        this.sendChar(nodeId, "\t");
      }
      else {
        this.sendChar(nodeId, event.key);
      }

      this.scrollToBottom();
    },

    handleKeyup(event) {
      if (event.key === "Control") {
        this.ctrlPressed = false;
      }
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

<style scoped>
.webshell-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #1e1e1e;
  color: #cccccc;
  font-family: "Fira Code", Consolas, monospace;
  border: 1px solid #333;
  border-radius: 4px;
  border-top: 3px solid #007acc;
}

.webshell-header {
  display: flex;
  align-items: center;
  background-color: #2d2d2d;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #333;
}

.webshell-header i {
  font-size: 1.2rem;
  margin-right: 0.5rem;
}

.webshell-header .title {
  font-weight: bold;
  font-size: 1rem;
}

.tabs {
  display: flex;
  background-color: #2d2d2d;
  border-bottom: 1px solid #333;
}

.tab-button {
  padding: 0.5rem 1rem;
  background: transparent;
  color: #cccccc;
  border: none;
  cursor: pointer;
  outline: none;
  transition: background-color 0.2s;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.tab-button.active {
  background-color: #1e1e1e;
  border-bottom: 2px solid #007acc;
}

.tab-button:hover {
  background-color: #333333;
}

.terminal-window {
  flex: 1;
  display: flex;
  position: relative;
  flex-direction: column;
  padding: 1rem;
  overflow: hidden;
}

.terminal-output {
  flex: 1;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.hidden-input {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 0;
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
  background-color: #cccccc;
}

.empty {
  border: 1px solid #cccccc;
}
</style>
