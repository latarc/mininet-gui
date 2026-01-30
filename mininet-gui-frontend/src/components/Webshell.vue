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
          Sniffer
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'logs' }"
          @click="activeView = 'logs'"
        >
          Logs
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: activeView === 'chat' }"
          @click="activeView = 'chat'"
        >
          Chat
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
          <strong>{{ message.role }}:</strong>
          <span class="chat-content">{{ message.content }}</span>
        </div>
      </div>
      <div class="chat-input">
        <textarea
          v-model="chatInput"
          placeholder="Ask the assistant to modify the topology..."
          @keydown.enter.exact.prevent="sendChat"
          :disabled="chatBusy"
          rows="2"
        ></textarea>
        <button :disabled="chatBusy" @click="sendChat">Send</button>
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
import { llmTools, runToolCalls } from "@/llm/actions";
import { buildSystemPrompt } from "@/llm/systemPrompt";

export default {
  components: { TrafficView },
  emits: ["viewChange"],
  props: {
    nodes: { type: Object, required: true },
    edges: { type: Object, default: null },
    snifferActive: { type: Boolean, default: false },
    preferredView: { type: String, default: null },
    focusNodeId: { type: String, default: null },
    openaiKey: { type: String, default: "" },
    llmHandlers: { type: Object, default: () => ({}) },
  },
  data() {
    return {
      terminals: {},
      fitAddons: {},
      terminalRefs: {},
      sockets: {},
      logTerminal: null,
      logFitAddon: null,
      logSocket: null,
      activeTab: null,
      backendWsUrl: import.meta.env.VITE_BACKEND_WS_URL,
      resizeObserver: null,
      isMinimized: false,
      panelHeight: 320,
      isResizing: false,
      activeView: "terminal",
      chatMessages: [
        { role: "system", content: "You are a network assistant. Use tools to create nodes and links when needed." },
      ],
      chatInput: "",
      chatBusy: false,
      chatError: "",
    };
  },
  computed: {
    nodeCount() {
      return this.getNodeList().length;
    },
  },
  watch: {
    nodes: {
      handler() {
        this.syncNodes();
      },
      deep: true,
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
    Object.values(this.terminals).forEach(term => term?.dispose());
    if (this.logTerminal) this.logTerminal.dispose();
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

    initLogTerminal() {
      if (this.logTerminal || !this.$refs.logTerminal) return;
      const term = new Terminal({
        convertEol: true,
        cursorBlink: false,
        disableStdin: true,
        fontFamily: "Fira Code, Consolas, monospace",
        fontSize: 12,
        theme: {
          background: "#1e1e1e",
          foreground: "#cccccc",
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
    },

    focusLogTerminal() {
      if (this.logTerminal) this.logTerminal.focus();
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
    },

    clearTerminals() {
      Object.values(this.sockets).forEach(ws => ws?.close());
      Object.values(this.terminals).forEach(term => term?.dispose());
      this.terminals = {};
      this.fitAddons = {};
      this.terminalRefs = {};
      this.sockets = {};
      this.activeTab = null;
    },
    async sendChat() {
      if (!this.chatInput.trim()) return;
      if (!this.openaiKey) {
        this.chatError = "OpenAI API key is missing. Add it in Settings.";
        return;
      }
      const userMessage = { role: "user", content: this.chatInput.trim() };
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
        if (!assistant) throw new Error("No assistant response.");
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
      const contextMessage = this.buildGraphContext();
      const payloadMessages = contextMessage
        ? [...messages, { role: "system", content: contextMessage }]
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
        throw new Error(text || "OpenAI request failed.");
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
        return buildSystemPrompt({ nodes: summarizedNodes, edges: summarizedEdges });
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
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
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
  flex: 0 0 auto;
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
  background: #1f1f1f;
  border: 1px solid #2d2d2d;
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
  background: #121212;
  color: #e5e5e5;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.85rem;
  resize: none;
  max-height: 140px;
  overflow: auto;
}

.chat-input button {
  background: #007acc;
  color: #fff;
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
  color: #f87171;
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
