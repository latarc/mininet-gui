<template>
  <div class="monitoring-view">
    <div class="monitoring-toolbar">
      <div class="monitoring-filters">
        <label class="monitoring-select">
          Node
          <select v-model="selectedNode">
            <option disabled value="">Select node</option>
            <option v-for="node in nodes" :key="node.id" :value="node.id">
              {{ node.id }}
            </option>
          </select>
        </label>
        <label class="monitoring-select">
          Interface
          <select v-model="selectedInterface" :disabled="!availableInterfaces.length">
            <option disabled value="">Select interface</option>
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
          <span>{{ isMonitoring ? "Stop Monitoring" : "Start Monitoring" }}</span>
        </button>
        <button
          class="monitoring-export"
          type="button"
          :disabled="!chartsReady || isExporting"
          @click="exportChartsAsPNG"
        >
          <span class="material-symbols-outlined">download</span>
          <span>{{ isExporting ? "Exportando…" : "Exportar gráficos" }}</span>
        </button>
        <span class="monitoring-status" :class="status">
          {{ statusMessage }}
        </span>
      </div>
    </div>

    <div class="monitoring-charts">
      <div class="chart-card">
        <div class="chart-label">TX (Gbps)</div>
        <div class="chart-container" ref="txChart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-label">RX (Gbps)</div>
        <div class="chart-container" ref="rxChart"></div>
      </div>
    </div>
  </div>
</template>

<script>
import Plotly from "plotly.js-dist-min";
import { getInterfaces } from "@/core/api";

export default {
  data() {
    return {
      nodes: [],
      selectedNode: "",
      selectedInterface: "",
      socket: null,
      status: "idle",
      statusMessage: "Select node and interface to begin monitoring.",
      backendWsUrl: import.meta.env.VITE_BACKEND_WS_URL,
      txChart: null,
      rxChart: null,
      maxSamples: 120,
      chartObserver: null,
      isExporting: false,
    };
  },
  computed: {
    availableInterfaces() {
      const node = this.nodes.find(item => item.id === this.selectedNode);
      return node ? node.intfs : [];
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
  },
  watch: {
    nodes: {
      handler(value) {
        if (!this.selectedNode && value.length) {
          this.selectedNode = value[0].id;
        }
      },
      deep: true,
    },
    selectedNode(nodeId) {
      const node = this.nodes.find(item => item.id === nodeId);
      if (node && node.intfs.length) {
        if (!node.intfs.includes(this.selectedInterface)) {
          this.selectedInterface = node.intfs[0];
        }
      } else {
        this.selectedInterface = "";
      }
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.initializeCharts();
    });
    this.loadInterfaces();
    this.setupChartObserver();
  },
  beforeUnmount() {
    this.stopMonitoring();
    this.destroyCharts();
    this.disconnectChartObserver();
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
              name: "TX",
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
              name: "RX",
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
      return {
        margin: { t: 20, b: 30, l: 40, r: 10 },
        plot_bgcolor: "#0b0f17",
        paper_bgcolor: "#0b0f17",
        font: { color: "#d1d5db" },
        xaxis: {
          title: "Time",
          type: "date",
          color: "#d1d5db",
          gridcolor: "rgba(255,255,255,0.08)",
          linecolor: "#2f2f37",
          tickcolor: "#9fa6af",
        },
        yaxis: {
          title: "Traffic (Gbps)",
          autorange: true,
          color: "#d1d5db",
          gridcolor: "rgba(255,255,255,0.08)",
          linecolor: "#2f2f37",
          tickcolor: "#9fa6af",
        },
        autosize: true,
        legend: {
          font: { color: "#d1d5db" },
        },
      };
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
      this.statusMessage = "Connecting to monitor...";
      const params = new URLSearchParams({
        node: this.selectedNode,
        intf: this.selectedInterface,
      });
      const ws = new WebSocket(`${this.backendWsUrl}/api/mininet/monitor?${params.toString()}`);
      this.socket = ws;

      ws.onopen = () => {
        this.status = "monitoring";
        this.statusMessage = `Streaming ${this.selectedNode} (${this.selectedInterface})`;
      };

      ws.onmessage = event => {
        let parsed = null;
        try {
          parsed = JSON.parse(event.data);
        } catch (error) {
          this.status = "error";
          this.statusMessage = event.data || "Monitoring connection dropped.";
          this.stopMonitoring();
          return;
        }
        this.appendSample(parsed);
      };

      ws.onerror = () => {
        if (this.status !== "error") {
          this.status = "error";
          this.statusMessage = "Monitoring connection error.";
        }
      };

      ws.onclose = () => {
        this.socket = null;
        if (this.status !== "error") {
          this.status = "idle";
          this.statusMessage = "Monitoring stopped.";
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
        this.statusMessage = "Monitoring stopped.";
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
      if (this.txChart) {
        Plotly.Plots.resize(this.txChart);
      }
      if (this.rxChart) {
        Plotly.Plots.resize(this.rxChart);
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
  flex: 1;
  min-height: 0;
  align-items: stretch;
}

.chart-card {
  flex: 1 1 320px;
  min-width: 240px;
  background: #111;
  border: 1px solid #222;
  border-radius: 8px;
  padding: 10px;
  min-height: 0;
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
}

.chart-container > div {
  width: 100%;
  height: 100%;
}
</style>
