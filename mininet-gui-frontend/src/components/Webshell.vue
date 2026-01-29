<template>
  <div
    class="webshell-container"
    :style="{ height: isMinimized ? '48px' : panelHeight + 'px' }"
  >
    <div v-show="!isMinimized" class="resize-handle-top" @mousedown.prevent="startResize"></div>
    <div class="webshell-header">
      <div class="webshell-title">
        <i class="mdi mdi-console"></i>
        <span class="title">Network Tools</span>
      </div>
      <div class="view-tabs">
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'terminal' }"
          @click="activeView = 'terminal'"
        >
          Terminal
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'traffic' }"
          @click="activeView = 'traffic'"
        >
          Traffic
        </button>
      </div>
      <div class="webshell-actions">
        <button class="icon-button" type="button" @click="toggleMinimize">
          <span class="material-symbols-outlined">{{ isMinimized ? "expand_less" : "expand_more" }}</span>
        </button>
      </div>
    </div>

    <div v-show="!isMinimized && activeView === 'terminal'" class="tabs">
      <button
        v-for="node in getNodeList()"
        :key="node.id"
        @click="setActiveTab(node.id)"
        :class="{ active: activeTab === node.id }"
        class="tab-button"
      >
        {{ node.id }}
      </button>
    </div>

    <div v-show="!isMinimized && activeView === 'terminal'" class="terminal-window" @click="focusActiveTerminal">
      <div
        v-for="node in getNodeList()"
        :key="node.id"
        :ref="el => setTerminalRef(node.id, el)"
        :class="['terminal-instance', { active: activeTab === node.id }]"
      ></div>
      <div v-if="getNodeList().length === 0" class="terminal-empty">
        No nodes available.
      </div>
    </div>
    <div v-show="!isMinimized && activeView === 'traffic'" class="traffic-window">
      <TrafficView :enabled="snifferActive" />
    </div>
  </div>
</template>

<script>
import "@xterm/xterm/css/xterm.css";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import TrafficView from "./TrafficView.vue";

export default {
  components: { TrafficView },
  props: {
    nodes: { type: Object, required: true },
    snifferActive: { type: Boolean, default: false },
  },
  data() {
    return {
      terminals: {},
      fitAddons: {},
      terminalRefs: {},
      sockets: {},
      activeTab: null,
      backendWsUrl: import.meta.env.VITE_BACKEND_WS_URL,
      resizeObserver: null,
      isMinimized: false,
      panelHeight: 320,
      isResizing: false,
      activeView: "terminal",
    };
  },
  watch: {
    nodes: {
      handler(newNodes) {
        this.syncNodes();
      },
      deep: true,
    },
    snifferActive(value) {
      if (value) this.activeView = "traffic";
    },
    activeView(value) {
      if (value === "terminal") {
        this.$nextTick(() => {
          if (this.activeTab) this.fitTerminal(this.activeTab);
        });
      }
    },
  },
  mounted() {
    this.syncNodes();
    this.resizeObserver = new ResizeObserver(() => {
      if (this.activeTab) this.fitTerminal(this.activeTab);
    });
  },
  beforeUnmount() {
    Object.values(this.sockets).forEach(ws => ws?.close());
    Object.values(this.terminals).forEach(term => term?.dispose());
    if (this.resizeObserver) this.resizeObserver.disconnect();
    window.removeEventListener("mousemove", this.handleResize);
    window.removeEventListener("mouseup", this.stopResize);
  },
  methods: {
    getNodeList() {
      return this.nodes?.get ? this.nodes.get() : [];
    },

    syncNodes() {
      const nodeList = this.getNodeList();
      if (nodeList.length === 0) {
        this.clearTerminals();
        return;
      }

      if (!this.activeTab) {
        this.activeTab = nodeList[0]?.id ?? null;
      }

      const existingIds = new Set(nodeList.map(node => node.id));
      Object.keys(this.terminals).forEach(nodeId => {
        if (!existingIds.has(nodeId)) {
          this.disposeTerminal(nodeId);
        }
      });
    },

    setTerminalRef(nodeId, el) {
      if (!el) return;
      this.terminalRefs[nodeId] = el;
      if (!this.terminals[nodeId]) {
        this.createTerminal(nodeId, el);
      }
      if (this.resizeObserver) this.resizeObserver.observe(el);
    },

    createTerminal(nodeId, el) {
      const term = new Terminal({
        convertEol: true,
        cursorBlink: true,
        fontFamily: "Fira Code, Consolas, monospace",
        fontSize: 13,
        theme: {
          background: "#1e1e1e",
          foreground: "#cccccc",
          cursor: "#cccccc",
          selection: "#264f78",
        },
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(el);
      fitAddon.fit();

      term.onData(data => {
        this.sendChar(nodeId, data);
      });

      this.terminals[nodeId] = term;
      this.fitAddons[nodeId] = fitAddon;
      this.initWebSocket(nodeId);

      if (this.activeTab === nodeId) this.focusActiveTerminal();
    },

    setActiveTab(nodeId) {
      this.activeTab = nodeId;
      if (!this.sockets[nodeId]) this.initWebSocket(nodeId);
      this.$nextTick(() => {
        this.fitTerminal(nodeId);
        this.focusActiveTerminal();
      });
    },

    initWebSocket(nodeId) {
      if (this.sockets[nodeId]) return;
      const ws = new WebSocket(`${this.backendWsUrl}/api/mininet/terminal/${nodeId}`);
      
      ws.onopen = () => console.log(`Connected to ${nodeId}`);
      ws.onmessage = event => this.handleTerminalData(nodeId, event.data);
      ws.onerror = error => console.error(`WebSocket error (${nodeId}):`, error);
      ws.onclose = () => console.log(`WebSocket closed (${nodeId})`);
      
      this.sockets[nodeId] = ws;
    },

    handleTerminalData(nodeId, data) {
      const term = this.terminals[nodeId];
      if (!term) return;
      term.write(data);
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

    focusActiveTerminal() {
      const term = this.terminals[this.activeTab];
      if (term) term.focus();
    },

    fitTerminal(nodeId) {
      const fitAddon = this.fitAddons[nodeId];
      if (fitAddon) fitAddon.fit();
    },

    disposeTerminal(nodeId) {
      if (this.resizeObserver && this.terminalRefs[nodeId]) {
        this.resizeObserver.unobserve(this.terminalRefs[nodeId]);
      }
      this.sockets[nodeId]?.close();
      this.terminals[nodeId]?.dispose();
      delete this.sockets[nodeId];
      delete this.terminals[nodeId];
      delete this.fitAddons[nodeId];
      delete this.terminalRefs[nodeId];
      if (this.activeTab === nodeId) this.activeTab = null;
    },

    toggleMinimize() {
      this.isMinimized = !this.isMinimized;
      if (!this.isMinimized) {
        this.$nextTick(() => {
          if (this.activeTab) this.fitTerminal(this.activeTab);
        });
      }
    },

    startResize(event) {
      if (this.isMinimized) return;
      this.isResizing = true;
      this.startY = event.clientY;
      this.startHeight = this.panelHeight;
      window.addEventListener("mousemove", this.handleResize);
      window.addEventListener("mouseup", this.stopResize);
    },

    handleResize(event) {
      if (!this.isResizing) return;
      const delta = this.startY - event.clientY;
      const nextHeight = Math.min(720, Math.max(160, this.startHeight + delta));
      this.panelHeight = nextHeight;
      if (this.activeTab) this.fitTerminal(this.activeTab);
    },

    stopResize() {
      this.isResizing = false;
      window.removeEventListener("mousemove", this.handleResize);
      window.removeEventListener("mouseup", this.stopResize);
    },

    clearTerminals() {
      Object.values(this.sockets).forEach(ws => ws?.close());
      Object.values(this.terminals).forEach(term => term?.dispose());
      this.terminals = {};
      this.fitAddons = {};
      this.terminalRefs = {};
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
  background-color: #1e1e1e;
  color: #cccccc;
  font-family: "Fira Code", Consolas, monospace;
  border: 1px solid #333;
  border-radius: 4px;
  border-top: 3px solid #007acc;
  position: relative;
}

.webshell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  background-color: #2d2d2d;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #333;
}

.webshell-title {
  display: flex;
  align-items: center;
}

.webshell-header i {
  font-size: 1.2rem;
  margin-right: 0.5rem;
}

.webshell-header .title {
  font-weight: bold;
  font-size: 1rem;
}

.webshell-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.view-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  margin-right: 8px;
}

.view-tab {
  border: 1px solid transparent;
  background: transparent;
  color: #cccccc;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.view-tab:hover {
  background-color: #333333;
}

.view-tab.active {
  border-color: #007acc;
  background-color: #1e1e1e;
  color: #ffffff;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #cccccc;
  cursor: pointer;
  border-radius: 4px;
}

.icon-button:hover {
  background-color: #333333;
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
  overflow: hidden;
}

.terminal-instance {
  flex: 1;
  display: none;
}

.terminal-instance.active {
  display: block;
  height: 100%;
}

.terminal-empty {
  padding: 1rem;
  color: #8a8a8a;
  font-size: 0.9rem;
}

.traffic-window {
  flex: 1;
  min-height: 0;
}

.resize-handle-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 8px;
  cursor: ns-resize;
  background: transparent;
  z-index: 2;
}
</style>
