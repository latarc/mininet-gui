<template>
  <div
    :class="['webshell-container', themeClass, { minimized: isMinimized }]"
    :style="{ height: isMinimized ? minimizedHeight + 'px' : panelHeight + 'px' }"
  >
    <div v-show="!isMinimized" class="resize-handle-top" @mousedown.prevent="startResize"></div>
    <div class="webshell-header">
      <div class="webshell-title">
        <i class="mdi mdi-console"></i>
        <span class="title">{{ $t("webshell.title") }}</span>
      </div>
      <div class="view-tabs">
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'terminal' }"
          @click="activeView = 'terminal'"
        >
          {{ $t("webshell.tabs.webshell") }}
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'traffic' }"
          @click="activeView = 'traffic'"
        >
          {{ $t("webshell.tabs.sniffer") }}
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'monitor' }"
          @click="activeView = 'monitor'"
        >
          {{ $t("webshell.tabs.monitoring") }}
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'logs' }"
          @click="activeView = 'logs'"
        >
          {{ $t("webshell.tabs.logs") }}
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'chat' }"
          @click="activeView = 'chat'"
        >
          {{ $t("webshell.tabs.chat") }}
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
        v-for="session in getSessionList()"
        :key="session.id"
        @click="setActiveTab(session.id)"
        :class="{ active: activeTab === session.id }"
        class="tab-button"
        type="button"
      >
        <span class="tab-label">{{ session.label || session.nodeId }}</span>
        <span
          class="tab-close"
          role="button"
          tabindex="0"
          :aria-label="$t('webshell.closeTerminal')"
          @click.stop="closeSession(session.id)"
          @keydown.enter.stop.prevent="closeSession(session.id)"
          @keydown.space.stop.prevent="closeSession(session.id)"
        >
          ×
        </span>
      </button>
    </div>

    <div v-show="!isMinimized && activeView === 'terminal'" class="terminal-window" @click="focusActiveTerminal">
      <div class="terminal-stack">
        <div
          v-for="session in getSessionList()"
          :key="session.id"
          :ref="el => setTerminalRef(session.id, session.nodeId, el)"
          :class="['terminal-instance', { active: activeTab === session.id }]"
        ></div>
        <div v-if="getSessionList().length === 0" class="terminal-empty">
          {{ $t("webshell.noSessions") }}
        </div>
      </div>
    </div>
    <div v-show="!isMinimized && activeView === 'traffic'" class="traffic-window">
      <TrafficView
        :enabled="snifferActive"
        :graphNodes="graphNodeList"
        :graphVersion="graphVersion"
        :theme="theme"
        @toggleSniffer="$emit('toggleSniffer')"
      />
    </div>
    <div v-show="!isMinimized && activeView === 'monitor'" class="monitoring-window">
      <MonitoringView :graphNodes="graphNodeList" :graphVersion="graphVersion" :theme="theme" />
    </div>
    <div v-show="!isMinimized && activeView === 'logs'" class="terminal-window" @click="focusLogTerminal">
      <div
        ref="logTerminal"
        class="terminal-instance active"
      ></div>
    </div>
    <div v-show="!isMinimized && activeView === 'chat'" class="chat-window">
      <div class="chat-messages" ref="chatMessages">
        <div
          v-for="(message, index) in chatMessages.filter(m => m.role !== 'system')"
          :key="index"
          class="chat-message"
          :class="`chat-${message.role}`"
        >
          <strong>{{ $t(`webshell.roles.${message.role}`) }}:</strong>
          <span class="chat-content">{{ message.content }}</span>
        </div>
      </div>
      <div class="chat-input">
        <textarea
          v-model="chatInput"
          :placeholder="$t('webshell.chatPlaceholder')"
          @keydown.enter.exact.prevent="sendChat"
          :disabled="chatBusy"
          rows="2"
        ></textarea>
        <button :disabled="chatBusy" @click="sendChat">{{ $t("actions.send") }}</button>
      </div>
      <p v-if="chatError" class="chat-error">{{ chatError }}</p>
    </div>
  </div>
</template>

<script>
import "@xterm/xterm/css/xterm.css";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import TrafficView from "./TrafficView.vue";
import MonitoringView from "./MonitoringView.vue";
import { llmTools, runToolCalls } from "@/llm/actions";
import { buildGraphStateMessage, buildSystemPrompt } from "@/llm/systemPrompt";

export default {
  components: { TrafficView, MonitoringView },
  emits: ["viewChange", "toggleSniffer", "closeSession", "minimizeChange"],
  props: {
    nodes: { type: Object, required: true },
    edges: { type: Object, default: null },
    snifferActive: { type: Boolean, default: false },
    terminalSessions: { type: Array, default: () => [] },
    preferredView: { type: String, default: null },
    focusNodeId: { type: String, default: null },
    minimized: { type: Boolean, default: false },
    openaiKey: { type: String, default: "" },
    llmHandlers: { type: Object, default: () => ({}) },
    theme: { type: String, default: "dark" },
  },
  data() {
    return {
      terminals: {},
      fitAddons: {},
      terminalRefs: {},
      sockets: {},
      sessionNodeIds: {},
      logTerminal: null,
      logFitAddon: null,
      logSocket: null,
      activeTab: null,
      backendWsUrl: import.meta.env.VITE_BACKEND_WS_URL,
      resizeObserver: null,
      isMinimized: false,
      minimizedHeight: 56,
      panelHeight: 320,
      isResizing: false,
      activeView: "terminal",
      chatMessages: [],
      chatInput: "",
      chatBusy: false,
      chatError: "",
      graphNodeList: [],
      graphVersion: 0,
      nodeDatasetRef: null,
      nodeDatasetHandler: null,
    };
  },
  computed: {
    nodeCount() {
      return this.getSessionList().length;
    },
    isLightTheme() {
      return this.theme === "light";
    },
    themeClass() {
      return this.isLightTheme ? "theme-light" : "theme-dark";
    },
    terminalTheme() {
      if (this.isLightTheme) {
        return {
          background: "#ffffff",
          foreground: "#2b2b2b",
          cursor: "#2b2b2b",
          selection: "#cce8ff",
        };
      }
      return {
        background: "#1e1e1e",
        foreground: "#cccccc",
        cursor: "#cccccc",
        selection: "#264f78",
      };
    },
  },
  watch: {
    nodes: {
      handler() {
        this.syncNodes();
        this.setupGraphWatcher();
      },
      immediate: true,
    },
    terminalSessions() {
      this.syncNodes();
    },
    snifferActive(value) {
      if (value) this.activeView = "traffic";
    },
    preferredView(value) {
      if (value) this.activeView = value;
    },
    focusNodeId(value) {
      if (value) {
        this.activeView = "terminal";
        this.setActiveTab(value);
      }
    },
    openaiKey() {
      this.chatError = "";
    },
    minimized(value) {
      this.isMinimized = !!value;
    },
    theme() {
      this.applyTerminalTheme();
    },
    activeView(value) {
      this.$emit("viewChange", value);
      if (value === "terminal") {
        this.$nextTick(() => {
          if (this.activeTab) this.fitTerminal(this.activeTab);
        });
      }
      if (value === "logs") {
        this.$nextTick(() => {
          this.initLogTerminal();
          this.initLogSocket();
          this.fitLogTerminal();
        });
      }
    },
  },
  mounted() {
    if (!this.chatMessages.length) {
      this.chatMessages = [
        { role: "system", content: this.$t("webshell.systemPrompt") },
      ];
    }
    this.isMinimized = !!this.minimized;
    this.syncNodes();
    if (this.preferredView) {
      this.activeView = this.preferredView;
    }
    if (this.focusNodeId) {
      this.activeView = "terminal";
      this.setActiveTab(this.focusNodeId);
    }
    this.resizeObserver = new ResizeObserver(() => {
      if (this.activeTab) this.fitTerminal(this.activeTab);
    });
  },
    beforeUnmount() {
      Object.values(this.sockets).forEach(ws => ws?.close());
      if (this.logSocket) this.logSocket.close();
      this.teardownGraphWatcher();
      Object.values(this.terminals).forEach(term => term?.dispose());
    if (this.logTerminal) this.logTerminal.dispose();
    if (this.resizeObserver) this.resizeObserver.disconnect();
    window.removeEventListener("mousemove", this.handleResize);
    window.removeEventListener("mouseup", this.stopResize);
  },
  methods: {
    getNodeList() {
      return [];
    },
    getSessionList() {
      return Array.isArray(this.terminalSessions) ? this.terminalSessions : [];
    },
    syncNodes() {
      const sessionList = this.getSessionList();
      if (sessionList.length === 0) {
        this.clearTerminals();
        return;
      }

      if (!this.activeTab) {
        this.activeTab = sessionList[0]?.id ?? null;
      }

      const existingIds = new Set(sessionList.map(session => session.id));
      Object.keys(this.terminals).forEach(sessionId => {
        if (!existingIds.has(sessionId)) {
          this.disposeTerminal(sessionId);
        }
      });
    },

    setTerminalRef(sessionId, nodeId, el) {
      if (!el) return;
      this.terminalRefs[sessionId] = el;
      if (!this.terminals[sessionId]) {
        this.createTerminal(sessionId, nodeId, el);
      }
      if (this.resizeObserver) this.resizeObserver.observe(el);
    },

    createTerminal(sessionId, nodeId, el) {
      const term = new Terminal({
        convertEol: true,
        cursorBlink: true,
        fontFamily: "Fira Code, Consolas, monospace",
        fontSize: 13,
        theme: this.terminalTheme,
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(el);
      fitAddon.fit();

      term.onData(data => {
        this.sendChar(sessionId, data);
      });

      this.terminals[sessionId] = term;
      this.fitAddons[sessionId] = fitAddon;
      this.sessionNodeIds[sessionId] = nodeId;
      this.initWebSocket(sessionId, nodeId);

      if (this.activeTab === sessionId) this.focusActiveTerminal();
    },

    setActiveTab(sessionId) {
      this.activeTab = sessionId;
      if (!this.sockets[sessionId]) this.initWebSocket(sessionId);
      this.$nextTick(() => {
        this.fitTerminal(sessionId);
        this.focusActiveTerminal();
      });
    },

    initWebSocket(sessionId, nodeId = null) {
      if (this.sockets[sessionId]) return;
      const targetNodeId = nodeId || this.sessionNodeIds[sessionId];
      if (!targetNodeId) return;
      const ws = new WebSocket(`${this.backendWsUrl}/api/mininet/terminal/${targetNodeId}`);
      
      ws.onopen = () => console.log(`Connected to ${targetNodeId} (${sessionId})`);
      ws.onmessage = event => this.handleTerminalData(sessionId, event.data);
      ws.onerror = error => console.error(`WebSocket error (${targetNodeId}):`, error);
      ws.onclose = () => console.log(`WebSocket closed (${targetNodeId})`);
      
      this.sockets[sessionId] = ws;
    },

    handleTerminalData(sessionId, data) {
      const term = this.terminals[sessionId];
      if (!term) return;
      term.write(data);
    },

    initLogTerminal() {
      if (this.logTerminal || !this.$refs.logTerminal) return;
      const term = new Terminal({
        convertEol: true,
        cursorBlink: false,
        disableStdin: true,
        fontFamily: "Fira Code, Consolas, monospace",
        fontSize: 12,
        theme: {
          background: this.terminalTheme.background,
          foreground: this.terminalTheme.foreground,
        },
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(this.$refs.logTerminal);
      fitAddon.fit();
      this.logTerminal = term;
      this.logFitAddon = fitAddon;
      if (this.resizeObserver) this.resizeObserver.observe(this.$refs.logTerminal);
    },

    initLogSocket() {
      if (this.logSocket) return;
      const ws = new WebSocket(`${this.backendWsUrl}/api/mininet/logs`);
      ws.onmessage = event => {
        if (this.logTerminal) {
          this.logTerminal.write(event.data + "\r\n");
        }
      };
      ws.onerror = error => console.error("Log WebSocket error:", error);
      ws.onclose = () => {
        this.logSocket = null;
      };
      this.logSocket = ws;
    },

    fitLogTerminal() {
      if (this.logFitAddon) this.logFitAddon.fit();
      const term = this.logTerminal;
      if (term && term.rows > 2) {
        term.resize(term.cols, term.rows - 2);
      }
    },

    focusLogTerminal() {
      if (this.logTerminal) this.logTerminal.focus();
    },
    applyTerminalTheme() {
      const theme = this.terminalTheme;
      Object.values(this.terminals || {}).forEach((term) => {
        if (term?.setOption) {
          term.setOption("theme", theme);
        }
      });
      if (this.logTerminal?.setOption) {
        this.logTerminal.setOption("theme", {
          background: theme.background,
          foreground: theme.foreground,
        });
      }
    },

    sendChar(sessionId, char) {
      const ws = this.sockets[sessionId];
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(char);
      } else {
        console.log(`WebSocket for ${sessionId} is not connected. Reconnecting...`);
        this.initWebSocket(sessionId);
      }
    },

    focusActiveTerminal() {
      const term = this.terminals[this.activeTab];
      if (term) term.focus();
    },

    fitTerminal(sessionId) {
      const fitAddon = this.fitAddons[sessionId];
      if (fitAddon) fitAddon.fit();
      const term = this.terminals[sessionId];
      if (term && term.rows > 2) {
        term.resize(term.cols, term.rows - 2);
      }
    },

    disposeTerminal(sessionId) {
      if (this.resizeObserver && this.terminalRefs[sessionId]) {
        this.resizeObserver.unobserve(this.terminalRefs[sessionId]);
      }
      this.sockets[sessionId]?.close();
      this.terminals[sessionId]?.dispose();
      delete this.sockets[sessionId];
      delete this.terminals[sessionId];
      delete this.fitAddons[sessionId];
      delete this.terminalRefs[sessionId];
      delete this.sessionNodeIds[sessionId];
      if (this.activeTab === sessionId) this.activeTab = null;
    },
    closeSession(sessionId) {
      const remaining = this.getSessionList().filter(session => session.id !== sessionId);
      if (this.activeTab === sessionId) {
        this.activeTab = remaining[0]?.id ?? null;
      }
      this.disposeTerminal(sessionId);
      this.$emit("closeSession", sessionId);
    },

    toggleMinimize() {
      this.isMinimized = !this.isMinimized;
      this.$emit("minimizeChange", this.isMinimized);
      if (!this.isMinimized) {
        this.$nextTick(() => {
          if (this.activeTab) this.fitTerminal(this.activeTab);
          if (this.activeView === "logs") this.fitLogTerminal();
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
      if (this.activeView === "terminal" && this.activeTab) this.fitTerminal(this.activeTab);
      if (this.activeView === "logs") this.fitLogTerminal();
    },

    stopResize() {
      this.isResizing = false;
      window.removeEventListener("mousemove", this.handleResize);
      window.removeEventListener("mouseup", this.stopResize);
      this.$nextTick(() => {
        if (this.activeView === "terminal" && this.activeTab) this.fitTerminal(this.activeTab);
        if (this.activeView === "logs") this.fitLogTerminal();
      });
    },

    clearTerminals() {
      Object.values(this.sockets).forEach(ws => ws?.close());
      Object.values(this.terminals).forEach(term => term?.dispose());
      this.terminals = {};
      this.fitAddons = {};
      this.terminalRefs = {};
      this.sockets = {};
      this.sessionNodeIds = {};
      this.activeTab = null;
    },
    setupGraphWatcher() {
      this.teardownGraphWatcher();
      const dataset = this.nodes;
      if (!dataset || typeof dataset.on !== "function" || typeof dataset.get !== "function") {
        this.graphNodeList = [];
        this.nodeDatasetRef = null;
        this.nodeDatasetHandler = null;
        return;
      }
      const handler = () => {
        this.updateGraphNodeList();
        this.graphVersion += 1;
      };
      this.nodeDatasetHandler = handler;
      this.nodeDatasetRef = dataset;
      ["add", "update", "remove"].forEach(event => {
        dataset.on(event, handler);
      });
      this.updateGraphNodeList();
    },
    teardownGraphWatcher() {
      const dataset = this.nodeDatasetRef;
      const handler = this.nodeDatasetHandler;
      if (!dataset || !handler) return;
      ["add", "update", "remove"].forEach(event => {
        if (typeof dataset.off !== "function") return;
        try {
          dataset.off(event, handler);
        } catch (error) {
          console.warn("Failed to detach watcher", event, error);
        }
      });
      this.nodeDatasetRef = null;
      this.nodeDatasetHandler = null;
    },
    updateGraphNodeList() {
      const dataset = this.nodeDatasetRef || this.nodes;
      if (!dataset?.get) {
        this.graphNodeList = [];
        return;
      }
      const entries = dataset.get();
      this.graphNodeList = entries.map(node => ({
        id: node.id,
        label: node.label || node.name || node.id,
        type: node.type,
        intfs: Array.isArray(node.intfs) ? [...node.intfs] : [],
      }));
    },
    async sendChat() {
      if (!this.chatInput.trim()) return;
      if (!this.openaiKey) {
        this.chatError = this.$t("webshell.errors.missingKey");
        return;
      }
      const graphStateMessage = this.buildGraphContext();
      const content = graphStateMessage
        ? `${this.chatInput.trim()}\n\n${graphStateMessage}`
        : this.chatInput.trim();
      const userMessage = { role: "user", content };
      console.log("[AI] user message", userMessage);
      this.chatMessages.push(userMessage);
      this.$nextTick(this.scrollChatToBottom);
      this.chatInput = "";
      this.chatError = "";
      this.chatBusy = true;
      try {
        let response = await this.callOpenAI(this.chatMessages);
        console.log("[AI] response", response);
        let assistant = response?.choices?.[0]?.message;
        if (!assistant) throw new Error(this.$t("webshell.errors.noAssistant"));
        console.log("[AI] assistant message", assistant);
        this.chatMessages.push(assistant);
        this.$nextTick(this.scrollChatToBottom);
        while (assistant?.tool_calls?.length) {
          console.log("[AI] tool_calls", assistant.tool_calls);
          const toolMessages = await runToolCalls(assistant.tool_calls, this.llmHandlers);
          console.log("[AI] tool responses", toolMessages);
          this.chatMessages.push(...toolMessages);
          this.$nextTick(this.scrollChatToBottom);
          response = await this.callOpenAI(this.chatMessages);
          console.log("[AI] follow-up response", response);
          assistant = response?.choices?.[0]?.message;
          if (!assistant) break;
          console.log("[AI] assistant message", assistant);
          this.chatMessages.push(assistant);
          this.$nextTick(this.scrollChatToBottom);
        }
      } catch (error) {
        this.chatError = error?.message || String(error);
      } finally {
        this.chatBusy = false;
      }
    },
    async callOpenAI(messages) {
      const systemPrompt = buildSystemPrompt();
      const payloadMessages = systemPrompt
        ? [{ role: "system", content: systemPrompt }, ...messages]
        : messages;
      console.log("[AI] sending messages", payloadMessages);
      const payload = {
        model: "gpt-4o-mini",
        messages: payloadMessages,
        tools: llmTools,
        tool_choice: "auto",
      };
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.openaiKey}`,
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || this.$t("webshell.errors.requestFailed"));
      }
      return response.json();
    },
    scrollChatToBottom() {
      const el = this.$refs.chatMessages;
      if (!el) return;
      el.scrollTop = el.scrollHeight;
    },
    buildGraphContext() {
      try {
        const nodes = this.nodes?.get ? this.nodes.get() : [];
        const edges = this.edges?.get ? this.edges.get() : [];
        const summarizedNodes = nodes.map((node) => ({
          id: node.id,
          type: node.type,
          name: node.name,
          label: node.label,
          ip: node.ip,
          controller: node.controller,
        }));
        const summarizedEdges = edges.map((edge) => ({
          from: edge.from,
          to: edge.to,
          title: edge.title,
          dashes: edge.dashes,
          color: edge.color,
        }));
        return buildGraphStateMessage({ nodes: summarizedNodes, edges: summarizedEdges });
      } catch (error) {
        console.warn("Failed to build graph context", error);
        return "";
      }
    },
  }
};
</script>

<style scoped>
.webshell-container {
  display: flex;
  flex-direction: column;
  background-color: var(--theme-webshell-bg);
  color: var(--theme-webshell-color);
  font-family: "Fira Code", Consolas, monospace;
  border: 1px solid var(--theme-webshell-border);
  border-radius: 4px;
  border-top: 3px solid #007acc;
  position: relative;
  min-height: 0;
  overflow: hidden;
}

.webshell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  background-color: var(--theme-webshell-header-bg);
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--theme-webshell-header-border);
  min-height: 44px;
}

.webshell-container.minimized .webshell-header {
  padding: 0.35rem 0.75rem;
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
  color: var(--theme-webshell-tab-color);
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.view-tab:hover {
  background-color: var(--theme-webshell-tab-hover);
}

.view-tab.active {
  border-color: #007acc;
  background-color: var(--theme-webshell-tab-active-bg);
  color: var(--theme-webshell-tab-active-color);
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--theme-webshell-icon-color);
  cursor: pointer;
  border-radius: 4px;
}

.icon-button:hover {
  background-color: #333333;
}

.tabs {
  display: flex;
  background-color: var(--theme-webshell-tabs-bg);
  border-bottom: 1px solid var(--theme-webshell-header-border);
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
}

.tab-button {
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--theme-webshell-tab-color);
  border: none;
  cursor: pointer;
  outline: none;
  transition: background-color 0.2s;
  font-size: 0.9rem;
  text-transform: uppercase;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-button.active {
  background-color: var(--theme-webshell-tab-active-bg);
  border-bottom: 2px solid #007acc;
}

.tab-button:hover {
  background-color: var(--theme-webshell-tab-hover);
}

.tab-label {
  pointer-events: none;
}

.tab-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  color: var(--theme-webshell-tab-color);
  font-size: 14px;
  line-height: 1;
}

.tab-close:hover {
  background: var(--theme-webshell-tab-hover);
  color: var(--theme-webshell-tab-active-color);
}

.terminal-window {
  flex: 1;
  display: flex;
  position: relative;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.terminal-stack {
  position: relative;
  flex: 1;
  min-height: 0;
}

.terminal-instance {
  position: absolute;
  inset: 0;
  display: none;
  min-height: 0;
  width: 100%;
  height: 100%;
}

.terminal-instance.active {
  display: block;
  height: 100%;
  min-height: 0;
}

.terminal-instance :deep(.xterm),
.terminal-instance :deep(.xterm-screen),
.terminal-instance :deep(.xterm-viewport) {
  height: 100%;
}

.terminal-instance :deep(.xterm-viewport) {
  padding-bottom: 8px;
  box-sizing: border-box;
}

.terminal-window :deep(.xterm-scrollable-element) {
  min-height: 100%;
  height: 100%;
}

.terminal-empty {
  padding: 1rem;
  color: var(--theme-traffic-empty-color);
  font-size: 0.9rem;
}

.traffic-window {
  flex: 1;
  min-height: 0;
}

.monitoring-window {
  flex: 1;
  min-height: 0;
}

.chat-window {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
}

.chat-messages {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.85rem;
}

.chat-message {
  background: var(--theme-webshell-chat-bg);
  border: 1px solid var(--theme-webshell-chat-border);
  padding: 8px 10px;
  border-radius: 8px;
}

.chat-content {
  white-space: pre-wrap;
}

.chat-user {
  border-color: #2a5d7a;
}

.chat-assistant {
  border-color: #2f6b3c;
}

.chat-tool {
  border-color: #5a3c6b;
  font-family: "Fira Code", Consolas, monospace;
  font-size: 0.75rem;
}

.chat-input {
  display: flex;
  gap: 8px;
}

.chat-input textarea {
  flex: 1;
  background: var(--theme-webshell-chat-input-bg);
  color: var(--theme-webshell-chat-input-color);
  border: 1px solid var(--theme-webshell-chat-input-border);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.85rem;
  resize: none;
  max-height: 140px;
  overflow: auto;
}

.chat-input button {
  background: var(--theme-webshell-chat-button-bg);
  color: var(--theme-webshell-chat-button-color);
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
}

.chat-input button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-error {
  color: var(--theme-webshell-chat-error);
  font-size: 0.8rem;
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
