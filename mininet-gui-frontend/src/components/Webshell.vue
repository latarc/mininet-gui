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
      ctrlPressed: false, // Track Control key state
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
      
      const ws = new WebSocket(`ws://192.168.56.101:8000/api/mininet/terminal/${nodeId}`);
      
      ws.onopen = () => console.log(`Connected to ${nodeId}`);
      ws.onmessage = event => this.handleTerminalData(nodeId, event.data);
      ws.onerror = error => console.error(`WebSocket error (${nodeId}):`, error);
      ws.onclose = () => console.log(`WebSocket closed (${nodeId})`);
      
      this.sockets[nodeId] = ws;
    },

    handleTerminalData(nodeId, data) {
      if (!this.terminals[nodeId]) this.terminals[nodeId] = "";

      // Handle backspace
      if (data === ("\b \b")) {
        this.terminals[nodeId] = this.terminals[nodeId].replace(/.$/, ""); // Remove last char
        this.sanitizedTerminals[nodeId] = this.terminals[nodeId];
        return;
      }

      // handle arrow left
      if (data === "\b") {
        if (this.userInputs[nodeId]?.length > 0) {
          this.userInputs[nodeId] = this.userInputs[nodeId].slice(0, -1); // Remove last character from input
          this.terminals[nodeId] += "\x1b[D"; // Move cursor left in display
        }
        this.sanitizedTerminals[nodeId] = this.terminals[nodeId];
        return;
      }


      // Ignore bell character
      if (data === "\u0007") return;

      // Clear screen sequence detection
      if (data.includes("[H\u001b[2J\u001b[3J\u001b")) {
        this.terminals[nodeId] = ""; // Clear display without losing history
        this.sanitizedTerminals[nodeId] = this.terminals[nodeId];
        return;
      }

      // **Filter out OSC sequences like terminal title changes**
      data = data.replace(/\x1b\]0;.*?\x07/g, "");

      // **Remove ANSI escape codes (cursor movements, colors, etc.)**
      data = data.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, "");
      data = data.replace(/\u001b/g, ""); // Remove any remaining ESC chars

      // Append sanitized data
      this.terminals[nodeId] += data;

      // Save sanitized version
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

      // Ignore Shift key presses and other modifier keys
      if (event.key === "Shift" || event.key === "CapsLock" || event.key === "Dead" || event.key === "Alt") {
        return;
      }

      if (event.key === "Control") {
        this.ctrlPressed = true;
        return;
      }

      if (this.ctrlPressed && event.key.toLowerCase() === "c") {
        this.sendChar(nodeId, "\x03"); // SIGINT (Ctrl+C)
      } else if (this.ctrlPressed && event.key.toLowerCase() === "l") {
        this.sendChar(nodeId, "\u001b[H\u001b[2J\u001b[3J\u001b"); // Clear screen (Ctrl+L)
      } else if (event.key === "Backspace") {
        this.sendChar(nodeId, "\b");
      } else if (event.key === "Enter") {
        this.sendChar(nodeId, "\n");
      } else if (event.key === "Tab") {
        this.sendChar(nodeId, "\t");
      } else if (event.key === "ArrowLeft") {
        // this.sendChar(nodeId, "\u001b[D"); // Move cursor left
      } else if (event.key === "ArrowRight") {
        // this.sendChar(nodeId, "\u001b[C"); // Move cursor right
      } else if (event.key === "ArrowUp") {
        // this.sendChar(nodeId, "\u001b[A"); // Move cursor up
      } else if (event.key === "ArrowDown") {
        // this.sendChar(nodeId, "\u001b[B"); // Move cursor down
      } else if (event.key === "Home") {
      } else if (event.key === "End") {
      } else if (event.key === "Delete") {
      } else {
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
