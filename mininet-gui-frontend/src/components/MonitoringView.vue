<template>
  <div class="monitoring-view">
    <div class="monitoring-toolbar">
      <div class="monitoring-filters">
        <label class="monitoring-select">
          {{ $t("monitoring.node") }}
          <select v-model="selectedNode">
            <option disabled value="">{{ $t("monitoring.selectNode") }}</option>
            <option v-for="node in nodeOptions" :key="node.id" :value="node.id">
              {{ node.label || node.id }}
            </option>
          </select>
        </label>
        <label class="monitoring-select">
          {{ $t("monitoring.interface") }}
          <select v-model="selectedInterface" :disabled="!availableInterfaces.length">
            <option disabled value="">{{ $t("monitoring.selectInterface") }}</option>
            <option v-for="intf in availableInterfaces" :key="intf" :value="intf">
              {{ intf }}
            </option>
          </select>
        </label>
      </div>
      <div class="monitoring-actions">
        <button
          class="monitoring-toggle"
          type="button"
          :class="{ active: isMonitoring }"
          :disabled="!canMonitor"
          @click="toggleMonitoring"
        >
          <span class="material-symbols-outlined">monitoring</span>
          <span>{{ isMonitoring ? $t("monitoring.stop") : $t("monitoring.start") }}</span>
        </button>
        <button
          class="monitoring-clear"
          type="button"
          :disabled="!chartsReady"
          @click="clearCharts"
        >
          <span class="material-symbols-outlined">delete_sweep</span>
          <span>{{ $t("monitoring.clearGraphs") }}</span>
        </button>
        <button
          class="monitoring-export"
          type="button"
          :disabled="!chartsReady || isExporting"
          @click="exportChartsAsPNG"
        >
          <span class="material-symbols-outlined">download</span>
          <span>{{ isExporting ? $t("monitoring.exporting") : $t("monitoring.exportCharts") }}</span>
        </button>
        <span class="monitoring-status" :class="status">
          {{ statusMessage }}
        </span>
      </div>
    </div>

    <div class="monitoring-charts">
        <div class="chart-card">
        <div class="chart-label">{{ $t("monitoring.txLabel") }}</div>
        <div class="chart-container" ref="txChart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-label">{{ $t("monitoring.rxLabel") }}</div>
        <div class="chart-container" ref="rxChart"></div>
      </div>
    </div>
  </div>
</template>

<script>
import Plotly from "plotly.js-dist-min";
import { getInterfaces } from "@/core/api";

export default {
  props: {
    graphNodes: { type: Array, default: () => [] },
    graphVersion: { type: Number, default: 0 },
    theme: { type: String, default: "dark" },
  },
  data() {
    return {
      nodes: [],
      selectedNode: "",
      selectedInterface: "",
      socket: null,
      status: "idle",
      statusMessage: "",
      backendWsUrl: import.meta.env.VITE_BACKEND_WS_URL,
      txChart: null,
      rxChart: null,
      maxSamples: 120,
      chartObserver: null,
      isExporting: false,
      interfaceTimer: null,
    };
  },
  computed: {
    nodeOptions() {
      const merged = [];
      const seen = new Set();
      this.graphNodes.forEach(graphNode => {
        const nodeType = graphNode.type;
        if (nodeType !== "sw" && nodeType !== "switch") return;
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
        const nodeType = backendNode.type;
        if (nodeType !== "sw" && nodeType !== "switch") return;
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
    currentNodeInfo() {
      return this.nodeOptions.find(item => item.id === this.selectedNode) || null;
    },
    availableInterfaces() {
      return this.currentNodeInfo?.intfs || [];
    },
    canMonitor() {
      return !!this.selectedNode && !!this.selectedInterface;
    },
    isMonitoring() {
      return this.socket && this.status === "monitoring";
    },
    chartsReady() {
      return !!(this.txChart && this.rxChart);
    },
    isLightTheme() {
      return this.theme === "light";
    },
  },
  watch: {
    graphNodes: {
      handler() {
        this.ensureSelectedNode();
      },
      deep: true,
      immediate: true,
    },
    graphVersion() {
      this.loadInterfaces();
    },
    theme() {
      this.applyChartTheme();
    },
    nodes: {
      handler() {
        this.refreshSelectedInterface();
      },
      deep: true,
    },
    selectedNode() {
      this.refreshSelectedInterface();
    },
  },
  mounted() {
    this.statusMessage = this.$t("monitoring.idleMessage");
    this.$nextTick(() => {
      this.initializeCharts();
    });
    this.loadInterfaces();
    this.interfaceTimer = setInterval(() => this.loadInterfaces(), 3000);
    this.setupChartObserver();
    window.addEventListener("resize", this.handleWindowResize);
  },
  beforeUnmount() {
    this.stopMonitoring();
    this.destroyCharts();
    this.disconnectChartObserver();
    if (this.interfaceTimer) {
      clearInterval(this.interfaceTimer);
      this.interfaceTimer = null;
    }
    window.removeEventListener("resize", this.handleWindowResize);
  },
  methods: {
    async loadInterfaces() {
      try {
        const response = await getInterfaces();
        this.nodes = response.nodes || [];
        if (!this.selectedNode && this.nodes.length) {
          this.selectedNode = this.nodes[0].id;
        }
      } catch (error) {
        this.nodes = [];
      }
    },
    ensureSelectedNode() {
      if (!this.nodeOptions.length) {
        this.selectedNode = "";
        return;
      }
      const exists = this.nodeOptions.some(node => node.id === this.selectedNode);
      if (!exists) {
        this.selectedNode = this.nodeOptions[0].id;
      }
    },
    refreshSelectedInterface() {
      const interfaces = this.availableInterfaces;
      if (interfaces.length) {
        if (!interfaces.includes(this.selectedInterface)) {
          this.selectedInterface = interfaces[0];
        }
      } else {
        this.selectedInterface = "";
      }
    },
    initializeCharts() {
      if (this.txChart) {
        Plotly.purge(this.txChart);
      }
      if (this.rxChart) {
        Plotly.purge(this.rxChart);
      }
      const config = { responsive: true, displayModeBar: false };

      if (this.$refs.txChart) {
        Plotly.newPlot(
          this.$refs.txChart,
          [
            {
              x: [],
              y: [],
              mode: "lines",
              name: this.$t("monitoring.txShort"),
              line: { color: "#00b4d8" },
            },
          ],
          this.createChartLayout(),
          config,
        );
        this.txChart = this.$refs.txChart;
        this.observeChart(this.$refs.txChart);
      }

      if (this.$refs.rxChart) {
        Plotly.newPlot(
          this.$refs.rxChart,
          [
            {
              x: [],
              y: [],
              mode: "lines",
              name: this.$t("monitoring.rxShort"),
              line: { color: "#ffb703" },
            },
          ],
          this.createChartLayout(),
          config,
        );
        this.rxChart = this.$refs.rxChart;
        this.observeChart(this.$refs.rxChart);
      }
    },

    createChartLayout() {
      const bg = this.isLightTheme ? "#f5f5f5" : "#0b0f17";
      const text = this.isLightTheme ? "#2b2b2b" : "#d1d5db";
      const grid = this.isLightTheme ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.08)";
      const axisLine = this.isLightTheme ? "#cfcfcf" : "#2f2f37";
      const tick = this.isLightTheme ? "#6b6b6b" : "#9fa6af";
      return {
        margin: { t: 20, b: 30, l: 40, r: 10 },
        plot_bgcolor: bg,
        paper_bgcolor: bg,
        font: { color: text },
        xaxis: {
          title: "Time",
          type: "date",
          color: text,
          gridcolor: grid,
          linecolor: axisLine,
          tickcolor: tick,
        },
        yaxis: {
          title: "Traffic (Gbps)",
          autorange: true,
          color: text,
          gridcolor: grid,
          linecolor: axisLine,
          tickcolor: tick,
        },
        autosize: true,
        legend: {
          font: { color: text },
        },
      };
    },
    applyChartTheme() {
      const layout = this.createChartLayout();
      if (this.txChart) {
        Plotly.relayout(this.txChart, layout);
      }
      if (this.rxChart) {
        Plotly.relayout(this.rxChart, layout);
      }
    },
    destroyCharts() {
      if (this.txChart) {
        Plotly.purge(this.txChart);
        this.txChart = null;
      }
      if (this.rxChart) {
        Plotly.purge(this.rxChart);
        this.rxChart = null;
      }
      this.disconnectChartObserver();
    },
    toggleMonitoring() {
      if (this.socket) {
        this.stopMonitoring();
      } else {
        this.startMonitoring();
      }
    },
    startMonitoring() {
      if (!this.canMonitor) {
        return;
      }
      this.status = "connecting";
      this.statusMessage = this.$t("monitoring.connecting");
      const params = new URLSearchParams({
        node: this.selectedNode,
        intf: this.selectedInterface,
      });
      const ws = new WebSocket(`${this.backendWsUrl}/api/mininet/monitor?${params.toString()}`);
      this.socket = ws;

      ws.onopen = () => {
        this.status = "monitoring";
        this.statusMessage = this.$t("monitoring.streaming", {
          node: this.selectedNode,
          intf: this.selectedInterface,
        });
      };

      ws.onmessage = event => {
        let parsed = null;
        try {
          parsed = JSON.parse(event.data);
        } catch (error) {
          this.status = "error";
          this.statusMessage = event.data || this.$t("monitoring.connectionDropped");
          this.stopMonitoring();
          return;
        }
        this.appendSample(parsed);
      };

      ws.onerror = () => {
        if (this.status !== "error") {
          this.status = "error";
          this.statusMessage = this.$t("monitoring.connectionError");
        }
      };

      ws.onclose = () => {
        this.socket = null;
        if (this.status !== "error") {
          this.status = "idle";
          this.statusMessage = this.$t("monitoring.stopped");
        }
      };
    },
    stopMonitoring() {
      if (this.socket) {
        this.socket.close();
      }
      this.socket = null;
      if (this.status !== "error") {
        this.status = "idle";
        this.statusMessage = this.$t("monitoring.stopped");
      }
    },
    setupChartObserver() {
      if (this.chartObserver) return;
      this.chartObserver = new ResizeObserver(() => {
        this.resizeCharts();
      });
    },
    disconnectChartObserver() {
      if (!this.chartObserver) return;
      this.chartObserver.disconnect();
      this.chartObserver = null;
    },
    observeChart(element) {
      if (element && this.chartObserver) {
        this.chartObserver.observe(element);
      }
    },
    resizeCharts() {
      this.updateChartSize(this.txChart, this.$refs.txChart);
      this.updateChartSize(this.rxChart, this.$refs.rxChart);
    },
    updateChartSize(chart, container) {
      if (!chart || !container) return;
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 360;
      Plotly.relayout(chart, { width, height });
      Plotly.Plots.resize(chart);
    },
    handleWindowResize() {
      this.resizeCharts();
    },
    clearCharts() {
      if (!this.chartsReady) return;
      try {
        Plotly.restyle(this.txChart, { x: [[]], y: [[]] });
        Plotly.restyle(this.rxChart, { x: [[]], y: [[]] });
      } catch (error) {
        console.error("Falha ao limpar gráficos:", error);
      }
    },
    appendSample(payload) {
      if (!payload) return;
      const timestamp = payload.ts ? new Date(payload.ts) : new Date();
      if (Number.isNaN(timestamp.getTime())) {
        return;
      }
      const tx = Number(payload.tx_gbps) || 0;
      const rx = Number(payload.rx_gbps) || 0;
      if (this.txChart) {
        Plotly.extendTraces(
          this.txChart,
          { x: [[timestamp]], y: [[tx]] },
          [0],
          this.maxSamples,
        );
      }
      if (this.rxChart) {
        Plotly.extendTraces(
          this.rxChart,
          { x: [[timestamp]], y: [[rx]] },
          [0],
          this.maxSamples,
        );
      }
    },
    async exportChartsAsPNG() {
      if (!this.chartsReady) return;
      this.isExporting = true;
      const exports = [
        this.downloadChart(this.txChart, "tx-traffic"),
        this.downloadChart(this.rxChart, "rx-traffic"),
      ];
      try {
        await Promise.all(exports);
      } finally {
        this.isExporting = false;
      }
    },
    async downloadChart(chart, prefix) {
      if (!chart) return;
      try {
        const width = chart.clientWidth || 800;
        const height = chart.clientHeight || 400;
        const dataUrl = await Plotly.toImage(chart, {
          format: "png",
          width,
          height,
          scale: 2,
          background: "#0b0f17",
        });
        const link = document.createElement("a");
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        link.href = dataUrl;
        link.download = `${prefix}-${timestamp}.png`;
        link.click();
      } catch (error) {
        console.error("Falha ao exportar gráfico:", error);
      }
    },
  },
};
</script>

<style scoped>
.monitoring-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 10px;
}

.monitoring-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #2a2a2a;
  background: #1a1a1a;
  flex-wrap: wrap;
  gap: 12px;
}

.monitoring-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.monitoring-select {
  display: flex;
  flex-direction: column;
  font-size: 0.75rem;
  color: #c8c8c8;
}

.monitoring-select select {
  margin-top: 4px;
  background: #0f0f0f;
  color: #ececec;
  border: 1px solid #333;
  padding: 6px 8px;
  border-radius: 4px;
  min-width: 140px;
}

.monitoring-select select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.monitoring-select select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.monitoring-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.monitoring-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #2a2a2a;
  padding: 6px 12px;
  background: #111;
  color: #fff;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.monitoring-toggle.active {
  border-color: #07c6ef;
  background: #043f5f;
  color: #cff2ff;
}

.monitoring-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.monitoring-export {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #2a2a2a;
  padding: 6px 12px;
  background: #1a1a1a;
  color: #fff;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s;
}

.monitoring-export:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.monitoring-export:not(:disabled):hover {
  background: #272727;
}

.monitoring-clear {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #2a2a2a;
  padding: 6px 12px;
  background: #1a1a1a;
  color: #fff;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s;
}

.monitoring-clear:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.monitoring-clear:not(:disabled):hover {
  background: #272727;
}

.monitoring-status {
  font-size: 0.8rem;
  color: #9da9b7;
}

.monitoring-status.monitoring {
  color: #9be2a5;
}

.monitoring-status.error {
  color: #ff6b6b;
}

.monitoring-charts {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 12px;
  flex: 1 1 0;
  height: 100%;
  min-height: 0;
  align-items: stretch;
}

.chart-card {
  flex: 1 1 320px;
  min-width: 240px;
  min-height: 0;
  height: 100%;
  background: #111;
  border: 1px solid #222;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-label {
  font-size: 0.8rem;
  color: #9da9b7;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chart-container {
  flex: 1;
  min-height: 0;
  height: 100%;
}

.chart-container > div {
  width: 100%;
  height: 100%;
}

:global(.theme-light) .monitoring-toolbar {
  background: #f5f5f5;
  border-bottom: 1px solid #d0d0d0;
}

:global(.theme-light) .monitoring-select {
  color: #2b2b2b;
}

:global(.theme-light) .monitoring-select select {
  background: #ffffff;
  color: #2b2b2b;
  border: 1px solid #d0d0d0;
}

:global(.theme-light) .monitoring-select select:focus {
  outline: 2px solid #007acc;
  box-shadow: 0 0 0 2px #007acc;
}

:global(.theme-light) .monitoring-toggle,
:global(.theme-light) .monitoring-export,
:global(.theme-light) .monitoring-clear {
  border: 1px solid #d0d0d0;
  background: #ffffff;
  color: #2b2b2b;
}

:global(.theme-light) .monitoring-toggle.active {
  border-color: #007acc;
  background: #e6f2ff;
  color: #0b2b3b;
}

:global(.theme-light) .monitoring-export:not(:disabled):hover,
:global(.theme-light) .monitoring-clear:not(:disabled):hover {
  background: #efefef;
}

:global(.theme-light) .monitoring-status {
  color: #6b6b6b;
}

:global(.theme-light) .monitoring-status.monitoring {
  color: #2f7d46;
}

:global(.theme-light) .monitoring-status.error {
  color: #c62828;
}

:global(.theme-light) .chart-card {
  background: #ffffff;
  border: 1px solid #d0d0d0;
}

:global(.theme-light) .chart-label {
  color: #6b6b6b;
}
</style>
