<template>
  <div class="traffic-view">
    <div class="traffic-toolbar">
      <button
        class="sniffer-toggle"
        type="button"
        :class="{ active: enabled }"
        @click="$emit('toggleSniffer')"
      >
        <span class="material-symbols-outlined">radar</span>
        <span>{{ enabled ? (connected ? $t("traffic.stopSniffer") : $t("traffic.connecting")) : $t("traffic.startSniffer") }}</span>
      </button>
      <div class="traffic-filters">
        <select v-model="selectedDevice" class="traffic-select">
          <option value="all">{{ $t("traffic.allDevices") }}</option>
          <option v-for="node in nodeOptions" :key="node.id" :value="node.id">
            {{ node.label || node.id }}
          </option>
        </select>
        <select v-model="selectedInterface" class="traffic-select">
          <option value="all">{{ $t("traffic.allInterfaces") }}</option>
          <option v-for="intf in availableInterfaces" :key="intf" :value="intf">
            {{ intf }}
          </option>
        </select>
        <select v-model="selectedProto" class="traffic-select">
          <option value="all">{{ $t("traffic.allProtocols") }}</option>
          <option value="IP">IP</option>
          <option value="IP6">IP6</option>
          <option value="ARP">ARP</option>
          <option value="TCP">TCP</option>
          <option value="UDP">UDP</option>
          <option value="ICMP">ICMP</option>
          <option value="ICMP6">ICMP6</option>
          <option value="DNS">DNS</option>
          <option value="DHCP">DHCP</option>
          <option value="HTTP">HTTP</option>
          <option value="HTTPS">HTTPS</option>
          <option value="SSH">SSH</option>
          <option value="TLS">TLS</option>
          <option value="LLDP">LLDP</option>
          <option value="OTHER">{{ $t("traffic.other") }}</option>
        </select>
        <input v-model="textFilter" class="traffic-input" :placeholder="$t('traffic.filterPlaceholder')" />
      </div>
      <div class="traffic-actions">
        <button class="traffic-button" type="button" @click="clearEvents" :disabled="events.length === 0">
          {{ $t("actions.clear") }}
        </button>
      </div>
    </div>
    <div class="traffic-table">
      <div class="traffic-row header">
        <span class="cell time">{{ $t("traffic.time") }}</span>
        <span class="cell node">{{ $t("traffic.device") }}</span>
        <span class="cell intf">{{ $t("traffic.interface") }}</span>
        <span class="cell proto">{{ $t("traffic.proto") }}</span>
        <span class="cell src">{{ $t("traffic.source") }}</span>
        <span class="cell dst">{{ $t("traffic.destination") }}</span>
        <span class="cell len">{{ $t("traffic.length") }}</span>
        <span class="cell info">{{ $t("traffic.info") }}</span>
      </div>
      <div class="traffic-body" ref="list">
        <div v-for="(item, index) in filteredEvents" :key="index" class="traffic-row">
          <span class="cell time">{{ formatTs(item.ts) }}</span>
          <span class="cell node">{{ item.node }}</span>
          <span class="cell intf">{{ item.intf }}</span>
          <span class="cell proto">{{ item.proto }}</span>
          <span class="cell src">{{ item.src }}</span>
          <span class="cell dst">{{ item.dst }}</span>
          <span class="cell len">{{ item.len ?? "" }}</span>
          <span class="cell info">{{ item.info || item.raw }}</span>
        </div>
        <div v-if="filteredEvents.length === 0" class="traffic-empty">
          {{ $t("traffic.noEvents") }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getInterfaces, getSnifferHistory } from "@/core/api";

export default {
  props: {
    enabled: { type: Boolean, default: false },
    graphNodes: { type: Array, default: () => [] },
    graphVersion: { type: Number, default: 0 },
    theme: { type: String, default: "dark" },
  },
  emits: ["toggleSniffer"],
  data() {
    return {
      socket: null,
      events: [],
      connected: false,
      backendWsUrl: import.meta.env.VITE_BACKEND_WS_URL,
      nodes: [],
      selectedDevice: "all",
      selectedInterface: "all",
      selectedProto: "all",
      textFilter: "",
      maxEvents: 1500,
    };
  },
  computed: {
    nodeOptions() {
      const merged = [];
      const seen = new Set();
      this.graphNodes.forEach(graphNode => {
        const backendNode = this.nodes.find(n => n.id === graphNode.id);
        merged.push({
          id: graphNode.id,
          label: graphNode.label || graphNode.name || graphNode.id,
          type: graphNode.type,
          intfs: backendNode?.intfs || graphNode.intfs || [],
        });
        seen.add(graphNode.id);
      });
      this.nodes.forEach(backendNode => {
        if (seen.has(backendNode.id)) return;
        merged.push({
          id: backendNode.id,
          label: backendNode.id,
          type: backendNode.type,
          intfs: backendNode.intfs || [],
        });
        seen.add(backendNode.id);
      });
      return merged;
    },
    availableInterfaces() {
      if (this.selectedDevice === "all") {
        const all = new Set();
        this.nodeOptions.forEach(node => node.intfs.forEach(intf => all.add(intf)));
        return Array.from(all).sort();
      }
      const node = this.nodeOptions.find(n => n.id === this.selectedDevice);
      return node ? node.intfs : [];
    },
    filteredEvents() {
      const text = this.textFilter.trim().toLowerCase();
      const items = this.events.filter(item => {
        if (this.selectedDevice !== "all" && item.node !== this.selectedDevice) return false;
        if (this.selectedInterface !== "all" && item.intf !== this.selectedInterface) return false;
        if (this.selectedProto !== "all") {
          if (this.selectedProto === "OTHER") {
            if (["IP", "IP6", "ARP"].includes(item.proto)) return false;
          } else if (item.proto !== this.selectedProto) {
            return false;
          }
        }
        if (text) {
          const hay = `${item.raw || ""} ${item.src || ""} ${item.dst || ""} ${item.info || ""}`.toLowerCase();
          if (!hay.includes(text)) return false;
        }
        return true;
      });
      return items.sort((a, b) => this.toEpochNs(a.ts) - this.toEpochNs(b.ts));
    },
  },
  watch: {
    enabled: {
      immediate: true,
      handler(value) {
        if (value) {
          this.connect();
        } else {
          this.disconnect();
          this.events = [];
        }
      },
    },
    graphNodes: {
      handler() {
        this.ensureSelectedDevice();
      },
      deep: true,
      immediate: true,
    },
    graphVersion() {
      this.loadInterfaces();
    },
    selectedDevice() {
      this.validateSelectedInterface();
    },
    nodes: {
      handler() {
        this.validateSelectedInterface();
      },
      deep: true,
    },
  },
  mounted() {
    this.loadInterfaces();
    this.loadHistory();
  },
  beforeUnmount() {
    this.disconnect();
  },
  methods: {
    async loadInterfaces() {
      try {
        const response = await getInterfaces();
        this.nodes = response.nodes || [];
      } catch (error) {
        this.nodes = [];
      }
    },
    ensureSelectedDevice() {
      if (this.selectedDevice === "all") return;
      const exists = this.nodeOptions.some(node => node.id === this.selectedDevice);
      if (!exists) {
        this.selectedDevice = "all";
      }
    },
    validateSelectedInterface() {
      if (this.selectedInterface === "all") return;
      const interfaces = this.availableInterfaces;
      if (!interfaces.includes(this.selectedInterface)) {
        this.selectedInterface = "all";
      }
    },
    async loadHistory() {
      try {
        const response = await getSnifferHistory();
        this.events = response.events || [];
      } catch (error) {
        this.events = [];
      }
    },
    connect() {
      if (this.socket) return;
      const ws = new WebSocket(`${this.backendWsUrl}/api/mininet/sniffer`);
      ws.onopen = () => {
        this.connected = true;
      };
      ws.onmessage = event => {
        let payload = null;
        try {
          payload = JSON.parse(event.data);
        } catch (error) {
          payload = { raw: String(event.data || ""), proto: "UNKNOWN" };
        }
        this.events.push(payload);
        if (this.events.length > this.maxEvents) {
          this.events.splice(0, this.events.length - this.maxEvents);
        }
        this.scrollToBottom();
      };
      ws.onerror = () => {
        this.connected = false;
      };
      ws.onclose = () => {
        this.connected = false;
        this.socket = null;
      };
      this.socket = ws;
    },
    disconnect() {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.connected = false;
    },
    clearEvents() {
      this.events = [];
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.list;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
    formatTs(value) {
      if (!value) return "";
      const ns = this.toEpochNs(value);
      if (!Number.isFinite(ns)) return String(value);
      const ms = Math.floor(ns / 1e6);
      const remNs = ns % 1e6;
      const date = new Date(ms);
      const hh = String(date.getHours()).padStart(2, "0");
      const mm = String(date.getMinutes()).padStart(2, "0");
      const ss = String(date.getSeconds()).padStart(2, "0");
      const frac = String(remNs).padStart(6, "0");
      return `${hh}:${mm}:${ss}.${frac}`;
    },
    toEpochNs(value) {
      if (!value) return NaN;
      if (typeof value === "number") return Math.floor(value);
      if (typeof value === "string") {
        // ISO string
        if (value.includes("T")) {
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) return NaN;
          return date.getTime() * 1e6;
        }
        const num = Number(value);
        if (!Number.isNaN(num)) return Math.floor(num);
      }
      return NaN;
    },
  },
};
</script>

<style scoped>
.traffic-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.traffic-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
  background-color: #2d2d2d;
  flex-wrap: wrap;
}

.traffic-status {
  font-size: 0.85rem;
  white-space: nowrap;
}

.traffic-status.active {
  color: #9cdcfe;
}

.traffic-status.inactive {
  color: #8a8a8a;
}

.traffic-filters {
  display: flex;
  gap: 6px;
  flex: 1;
  flex-wrap: wrap;
}

.traffic-select,
.traffic-input {
  background: #1e1e1e;
  color: #cccccc;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 0.8rem;
}

.traffic-select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.traffic-select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.traffic-input {
  min-width: 180px;
  flex: 1;
}

.traffic-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.traffic-button {
  border: 1px solid #333;
  background: #1e1e1e;
  color: #cccccc;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.traffic-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sniffer-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #333;
  background: #2d2d2d;
  color: #cccccc;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.sniffer-toggle.active {
  border-color: #007acc;
  background: #0b2b3b;
  color: #e6f2ff;
  box-shadow: 0 0 0 1px #007acc;
}

.traffic-table {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.traffic-body {
  overflow-y: auto;
  flex: 1;
}

.traffic-row {
  display: grid;
  grid-template-columns: 110px 90px 120px 60px 1fr 1fr 70px 2fr;
  gap: 8px;
  padding: 6px 12px;
  font-family: "Fira Code", Consolas, monospace;
  font-size: 0.78rem;
  color: #cccccc;
  align-items: center;
}

.traffic-row:nth-child(even) {
  background: #1f1f1f;
}

.traffic-row.header {
  font-weight: 600;
  background: #262626;
  border-bottom: 1px solid #333;
  position: sticky;
  top: 0;
  z-index: 1;
}

.cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.traffic-empty {
  padding: 1rem;
  color: #8a8a8a;
}

:global(.theme-light) .traffic-toolbar {
  background-color: #f5f5f5;
  border-bottom: 1px solid #d0d0d0;
}

:global(.theme-light) .traffic-status.active {
  color: #0b6fa5;
}

:global(.theme-light) .traffic-status.inactive {
  color: #6b6b6b;
}

:global(.theme-light) .traffic-select,
:global(.theme-light) .traffic-input {
  background: #ffffff;
  color: #2b2b2b;
  border: 1px solid #d0d0d0;
}

:global(.theme-light) .traffic-select:focus {
  outline: 2px solid #007acc;
  box-shadow: 0 0 0 2px #007acc;
}

:global(.theme-light) .traffic-button {
  border: 1px solid #d0d0d0;
  background: #ffffff;
  color: #2b2b2b;
}

:global(.theme-light) .sniffer-toggle {
  border: 1px solid #d0d0d0;
  background: #f5f5f5;
  color: #2b2b2b;
}

:global(.theme-light) .sniffer-toggle.active {
  border-color: #007acc;
  background: #e6f2ff;
  color: #0b2b3b;
  box-shadow: 0 0 0 1px #007acc;
}

:global(.theme-light) .traffic-row {
  color: #2b2b2b;
}

:global(.theme-light) .traffic-row:nth-child(even) {
  background: #f5f5f5;
}

:global(.theme-light) .traffic-row.header {
  background: #efefef;
  border-bottom: 1px solid #d0d0d0;
}

:global(.theme-light) .traffic-empty {
  color: #6b6b6b;
}
</style>
