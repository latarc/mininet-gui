<script setup>
import { Network } from "vis-network/peer";
import { DataSet } from "vis-data/peer";

import {
  getHosts,
  getSwitches,
  getControllers,
  getNats,
  getRouters,
  getEdges,
  getNodeStats,
  deployHost,
  deployNat,
  deployRouter,
  deployLink,
  deployController,
  deploySwitch,
  assocSwitch,
  updateController,
  requestStartNetwork,
  requestStopNetwork,
  requestFullResetNetwork,
  requestRunPingall,
  runIperf,
  deleteNode,
  deleteLink,
  updateNodePosition,
  requestExportNetwork,
  requestExportMininetScript,
  requestImportNetwork,
  removeAssociation,
  getAddressingPlan,
  getSnifferState,
  getHealthStatus,
  startSniffer,
  stopSniffer,
  exportSnifferPcap,
  getBackendVersion,
  getRyuApps,
} from "../core/api";
import { options } from "../core/options";
import Side from "./Side.vue";
import Modal from "./Modal.vue";
import Webshell from "./Webshell.vue";
import NodeStats from "./NodeStats.vue";
import LinkStats from "./LinkStats.vue";
import PingallResults from "./PingallResults.vue";
import ControllerForm from "./ControllerForm.vue";
import TopologyForm from "./TopologyForm.vue";
import frontendPackage from "../../package.json";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

import switchImg from "@/assets/light-switch.svg";
import switchOvsImg from "@/assets/light-switch-ovs.svg";
import switchOvsBridgeImg from "@/assets/light-switch-ovsbridge.svg";
import switchUserImg from "@/assets/light-switch-user.svg";
import hostImg from "@/assets/light-host.svg";
import natImg from "@/assets/light-nat.svg";
import routerImg from "@/assets/light-router.svg";
import logoImage from "@/assets/logo-mininet-gui.png";
</script>

<template>
  <div class="app-shell">
    <div v-if="!mininetConnected" class="health-overlay">
      <div class="health-overlay__card">
        <p>Mininet backend is disconnected. Actions are disabled until the service recovers.</p>
        <button type="button" class="menu-action health-overlay__retry" @click="refreshBackendHealth">
          Retry
        </button>
      </div>
    </div>
    <div ref="topbar" class="topbar">
      <div class="topbar-title">Mininet GUI</div>
      <div class="menu-bar">
        <div class="menu-item-wrapper">
          <button
            type="button"
            class="menu-item"
            :class="{ open: fileMenuOpen }"
            @click.stop="toggleFileMenu"
          >
            File
          </button>
          <div v-if="fileMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleNewTopology">
              New Topology
            </button>
            <button type="button" class="menu-action" @click="handleOpenTopology">
              Open Topology...
            </button>
            <button type="button" class="menu-action" @click="handleSaveTopology">
              Save Topology As...
            </button>
            <div class="menu-separator"></div>
            <button type="button" class="menu-action" @click="handleExportScript">
              Export Topology as Mininet Script
            </button>
            <button type="button" class="menu-action" @click="handleExportSniffer">
              Export Sniffer (PCAP)
            </button>
            <button type="button" class="menu-action" @click="handleExportPng">
              Export Topology as PNG
            </button>
            <button type="button" class="menu-action" @click="handleExportAddressingPlan">
              Export Addressing Plan (PDF)
            </button>
            <div class="menu-separator"></div>
            <button type="button" class="menu-action" @click="handleOpenSettings">
              Settings
            </button>
          </div>
        </div>
        <div class="menu-item-wrapper">
          <button
            type="button"
            class="menu-item"
            :class="{ open: viewMenuOpen }"
            @click.stop="toggleViewMenu"
          >
            View
          </button>
          <div v-if="viewMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleCollapseAllViews">
              Collapse all views
            </button>
            <button type="button" class="menu-action" @click="handleExpandAllViews">
              Expand all views
            </button>
            <div class="menu-separator"></div>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showHosts" @change="handleShowHostsSetting" />
              Show hosts
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showControllers" @change="handleShowControllersSetting" />
              Show controllers
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showSpecialSwitches" @change="persistSettings" />
              Show special switches
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showSpecialControllers" @change="persistSettings" />
              Show special controllers
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showHostIp" @change="persistSettings" />
              Show host IP addresses
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showSwitchDpids" @change="persistSettings" />
              Show switch DPIDs
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showPortLabels" @change="persistSettings" />
              Show port labels
            </label>
          </div>
        </div>
        <div class="menu-item-wrapper">
          <button
            type="button"
            class="menu-item"
            :class="{ open: runMenuOpen }"
            @click.stop="toggleRunMenu"
          >
            Run
          </button>
          <div v-if="runMenuOpen" class="menu-dropdown" @click.stop>
            <button
              type="button"
              class="menu-action"
              @click="handleStartNetwork"
              :disabled="networkStarted || networkCommandInFlight || !mininetConnected"
            >
              Start Network
            </button>
            <button
              type="button"
              class="menu-action"
              @click="handleStopNetwork"
              :disabled="!networkStarted || networkCommandInFlight || !mininetConnected"
            >
              Stop Network
            </button>
            <button
              type="button"
              class="menu-action"
              @click="handleRestartNetwork"
              :disabled="networkCommandInFlight || !mininetConnected"
            >
              Restart Network
            </button>
          </div>
        </div>
        <div class="menu-item-wrapper">
          <button
            type="button"
            class="menu-item"
            :class="{ open: toolsMenuOpen }"
            @click.stop="toggleToolsMenu"
          >
            Tools
          </button>
          <div v-if="toolsMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleRunIperf">
              Run Iperf
            </button>
            <button type="button" class="menu-action" @click="handleRunPingall">
              Run Pingall
            </button>
            <button type="button" class="menu-action" @click="handleGenerateTopology">
              Generate Topology
            </button>
            <div class="menu-separator"></div>
            <button type="button" class="menu-action" @click="handleStartSniffer">
              Start Sniffer
            </button>
            <button type="button" class="menu-action" @click="handleStopSniffer">
              Stop Sniffer
            </button>
          </div>
        </div>
        <div class="menu-item-wrapper">
          <button
            type="button"
            class="menu-item"
            :class="{ open: helpMenuOpen }"
            @click.stop="toggleHelpMenu"
          >
            Help
          </button>
          <div v-if="helpMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleOpenUsage">
              Usage
            </button>
            <button type="button" class="menu-action" @click="handleOpenDocumentation">
              Open documentation
            </button>
            <button type="button" class="menu-action" @click="handleOpenAbout">
              About
            </button>
          </div>
        </div>
      </div>
      <input
        ref="topologyFileInput"
        type="file"
        accept=".json"
        class="menu-file-input"
        @change="handleFileUpload"
      />
    </div>
    <div class="layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- Side panel (left) -->

        <div class="side-container">
        <Side
          @runPingall="showPingallModal"
          @runIperf="showIperfModal"
          @closeAllActiveModes="closeAllActiveModes"
          @toggleShowHosts="toggleShowHosts"
          @toggleShowControllers="toggleShowControllers"
          @createTopology="showTopologyFormModal"
          @toggleSidebar="handleSidebarToggle"
          @doSelectAll="doSelectAll"
          @toggleAddEdgeMode="handleToggleAddEdgeMode"
          @deleteSelected="doDeleteSelected"
          @keydown.ctrl.a.prevent="doSelectAll"
            :networkStarted="networkStarted"
            :networkConnected="mininetConnected"
            :showSpecialSwitches="settings.showSpecialSwitches"
            :showSpecialControllers="settings.showSpecialControllers"
            :addEdgeMode="addEdgeMode"
            :pingallRunning="pingallRunning"
            :iperfRunning="iperfBusy"
          />
        </div>
      
      <!-- Main Content (Graph + WebShell) -->
      <div class="main-content">
      <div ref="graphWrapper" class="graph-wrapper">
        <div ref="graph" id="network-graph" class="network-graph"
        @drop.prevent="handleDrop"
        @dragenter.prevent
        @dragover.prevent
        @click="hideContextMenu"
        @keydown.esc="closeAllActiveModes"
        @keydown.h="toggleShowHosts"
        @keydown.c="toggleShowControllers"
        @keydown.e="enterAddEdgeMode"
        @keydown.d="doDeleteSelected"
        @keydown.delete="doDeleteSelected"
        @keydown.ctrl.a.prevent="doSelectAll"
        ></div>
        <div
          v-show="selectionBox.active"
          class="selection-rect"
          :style="selectionRectStyle"
        ></div>
      </div>
      <div
        v-if="contextMenu.visible"
        class="node-context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <button type="button" class="node-context-item" @click="openWebshellFromMenu">
          Open Webshell
        </button>
        <button type="button" class="node-context-item" @click="openNodeStatsFromMenu">
          View Node Stats
        </button>
      </div>

      <!-- WebShell at the bottom -->
      <webshell
        class="webshell"
        :nodes="nodes"
        :edges="edges"
        :snifferActive="snifferActive"
        :terminalSessions="terminalSessions"
        :preferredView="webshellView"
        :focusNodeId="webshellFocusId"
        :minimized="webshellMinimized"
        :openaiKey="settings.openaiApiKey"
        :llmHandlers="llmHandlers"
        @viewChange="handleWebshellViewChange"
        @toggleSniffer="toggleSniffer"
        @minimizeChange="handleWebshellMinimizeChange"
        @closeSession="handleCloseSession"
      />
      </div>
    </div>
    <div class="status-bar">
      <div class="status-bar__right">
        <span
          class="status-dot"
          :class="mininetConnected ? 'status-dot--started' : 'status-dot--stopped'"
        ></span>
        <div class="status-bar__text">
          <span class="status-bar__primary">
            {{ mininetConnected ? "Connected to Mininet" : "Disconnected" }}
          </span>
          <span class="status-bar__version">
            Mininet {{ mininetVersion || "unknown" }}
          </span>
          <span class="status-bar__network">
            <span class="network-state-dot" :class="networkStateIndicator"></span>
            Network {{ networkStarted ? "Started" : "Stopped" }}
          </span>
          <span class="status-bar__counts">
            Hosts {{ networkCounts.hosts }} · Controllers {{ networkCounts.controllers }} · Switches {{ networkCounts.switches }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <modal
      :show="showModal"
      @close="closeModal"
      @keydown.esc="closeModal"
    >
      <template #header>
        <h3>{{ modalHeader }}</h3>
      </template>
      <template #body>
        <node-stats
          v-if="modalOption === 'nodeStats'"
          :stats="modalData"
          @hostUpdated="handleHostUpdated"
          @editController="showControllerEditModal"
        />
        <link-stats v-if="modalOption === 'linkStats'" :link="modalData" @linkUpdated="handleLinkUpdated" />
        <pingall-results v-if="modalOption === 'pingall'" :pingResults="modalData" />
        <div v-if="modalOption === 'iperf'" class="iperf-modal">
          <div class="iperf-form">
            <label class="iperf-label" for="iperf-client">Client</label>
            <select id="iperf-client" v-model="iperfForm.client" class="iperf-select">
              <option value="" disabled>Select client host</option>
              <option v-for="host in Object.values(hosts)" :key="host.id" :value="host.id">
                {{ host.id }}
              </option>
            </select>
            <label class="iperf-label" for="iperf-server">Server</label>
            <select id="iperf-server" v-model="iperfForm.server" class="iperf-select">
              <option value="" disabled>Select server host</option>
              <option v-for="host in Object.values(hosts)" :key="host.id" :value="host.id">
                {{ host.id }}
              </option>
            </select>
            <label class="iperf-label" for="iperf-proto">Protocol</label>
            <select id="iperf-proto" v-model="iperfForm.l4_type" class="iperf-select">
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
            </select>
            <label class="iperf-label" for="iperf-duration">Duration (s)</label>
            <input
              id="iperf-duration"
              v-model.number="iperfForm.seconds"
              class="iperf-select"
              type="number"
              min="1"
            />
            <label class="iperf-label" for="iperf-udp-bw">UDP BW (e.g. 10M)</label>
            <input
              id="iperf-udp-bw"
              v-model="iperfForm.udp_bw"
              class="iperf-select"
              type="text"
              :disabled="iperfForm.l4_type !== 'UDP'"
              placeholder="10M"
            />
            <label class="iperf-label" for="iperf-format">Format (K/M/G)</label>
            <input
              id="iperf-format"
              v-model="iperfForm.fmt"
              class="iperf-select"
              type="text"
              placeholder="M"
            />
            <label class="iperf-label" for="iperf-port">Port</label>
            <input
              id="iperf-port"
              v-model.number="iperfForm.port"
              class="iperf-select"
              type="number"
              min="1"
              max="65535"
            />
            <button
              class="iperf-run"
              type="button"
              :disabled="iperfBusy || !iperfForm.client || !iperfForm.server || iperfForm.client === iperfForm.server"
              @click="runIperfTest"
            >
              {{ iperfBusy ? "Running..." : "Run Iperf" }}
            </button>
            <p v-if="iperfError" class="iperf-error">{{ iperfError }}</p>
          </div>
          <div v-if="iperfResult" class="iperf-result">
            <h4>Result</h4>
            <pre>{{ formatIperfResult(iperfResult) }}</pre>
          </div>
        </div>
        <controller-form
          v-if="modalOption === 'controllerForm'"
          :preset-type="controllerFormPreset"
          :ryu-apps="ryuApps"
          :controller="controllerFormData"
          @form-submit="handleControllerFormSubmit"
          @form-update="handleControllerFormUpdate"
        />
        <topology-form v-if="modalOption === 'topologyForm'" :controllers="controllers" @form-submit="handleTopologyFormSubmit" />
        <div v-if="modalOption === 'usage'" class="help-modal">
          <div class="help-modal__tabs">
            <button type="button" :class="{ active: helpTab === 'welcome' }" @click="helpTab = 'welcome'">Welcome</button>
            <button type="button" :class="{ active: helpTab === 'shortcuts' }" @click="helpTab = 'shortcuts'">Shortcuts</button>
            <button type="button" :class="{ active: helpTab === 'devices' }" @click="helpTab = 'devices'">Devices</button>
          </div>
          <div v-if="helpTab === 'welcome'" class="help-tab">
            <p>Drag hosts, switches, or controllers from the sidebar onto the canvas to add devices.</p>
            <p>Use right/middle click to pan and the mouse wheel to zoom.</p>
            <p>Right-click a node to open its web shell or view stats.</p>
            <p>The Run menu starts, stops, or restarts Mininet without erasing the topology.</p>
          </div>
          <div v-if="helpTab === 'shortcuts'" class="help-tab">
            <p>H – toggle host visibility.</p>
            <p>C – toggle controllers.</p>
            <p>E – enter edge mode (click two nodes to connect).</p>
            <p>D/Delete – remove selection.</p>
            <p>Ctrl+A – select all nodes.</p>
            <p>Esc – cancel a mode or close the modal.</p>
          </div>
          <div v-if="helpTab === 'devices'" class="help-tab">
            <p>Host – emulates a Linux host.</p>
            <p>Switch – standard or special switch types (Ovskernel, OVS, user, bridge).</p>
            <p>Controller – default controller or remote/Ryu-based ones.</p>
            <p>Router – Linux router with IP forwarding.</p>
            <p>NAT – network address translation box.</p>
          </div>
        </div>
        <div v-if="modalOption === 'about'" class="help-modal">
          <img :src="logoImage" alt="Mininet GUI logo" class="help-modal__logo" />
          <h4>Mininet GUI</h4>
          <p>Frontend version: {{ frontendVersion }}</p>
          <p>Backend version: {{ backendVersion }}</p>
          <p>Mininet version: {{ mininetVersion }}</p>
          <p>Authors: Lucas Schneider, Emidio Neto, Felipe Dantas</p>
          <p>
            Repository:
            <a
              class="help-link"
              href="https://github.com/latarc/mininet-gui"
              target="_blank"
              rel="noreferrer"
            >
              https://github.com/latarc/mininet-gui
            </a>
          </p>
          <p>License: MIT</p>
        </div>
        <div v-if="modalOption === 'settings'" class="settings-modal">
          <div class="settings-group">
            <label class="settings-toggle">
              <input type="checkbox" v-model="settings.showHosts" @change="handleShowHostsSetting" />
              <span>Show hosts</span>
            </label>
            <label class="settings-toggle">
              <input type="checkbox" v-model="settings.showControllers" @change="handleShowControllersSetting" />
              <span>Show controllers</span>
            </label>
            <label class="settings-toggle">
              <input type="checkbox" v-model="settings.showSpecialSwitches" @change="persistSettings" />
              <span>Show special switches</span>
            </label>
            <label class="settings-toggle">
              <input type="checkbox" v-model="settings.showSpecialControllers" @change="persistSettings" />
              <span>Show special controllers</span>
            </label>
            <label class="settings-toggle">
              <input type="checkbox" v-model="settings.showHostIp" @change="persistSettings" />
              <span>Show host IP addresses</span>
            </label>
            <label class="settings-toggle">
              <input type="checkbox" v-model="settings.showSwitchDpids" @change="persistSettings" />
              <span>Show switch DPIDs</span>
            </label>
            <label class="settings-input">
              <span>OpenAI API Key</span>
              <input
                type="password"
                v-model="settings.openaiApiKey"
                @change="persistSettings"
                placeholder="sk-..."
              />
            </label>
            <div class="settings-link">
              <div class="settings-link-title">Default Link Attributes</div>
              <div class="settings-link-grid">
                <label>
                  Bandwidth (Mbps)
                  <input type="number" v-model="settings.linkOptions.bw" @change="persistSettings" min="0" />
                </label>
                <label>
                  Delay (ms)
                  <input type="number" v-model="settings.linkOptions.delay" @change="persistSettings" min="0" />
                </label>
                <label>
                  Jitter (ms)
                  <input type="number" v-model="settings.linkOptions.jitter" @change="persistSettings" min="0" />
                </label>
                <label>
                  Loss (%)
                  <input type="number" v-model="settings.linkOptions.loss" @change="persistSettings" min="0" max="100" />
                </label>
                <label>
                  Max Queue
                  <input type="number" v-model="settings.linkOptions.max_queue_size" @change="persistSettings" min="0" />
                </label>
                <label class="settings-toggle settings-inline">
                  <input type="checkbox" v-model="settings.linkOptions.use_htb" @change="persistSettings" />
                  <span>Use HTB</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div v-if="modalOption === 'confirmReset'" class="confirm-reset">
          <p class="confirm-reset__text">
            Are you sure you want to reset the topology? This action cannot be undone.
          </p>
          <div class="confirm-reset__actions">
            <button class="confirm-reset__button confirm-reset__button--cancel" @click="closeModal">
              Cancel
            </button>
            <button class="confirm-reset__button confirm-reset__button--danger" @click="confirmResetTopology">
              Reset Topology
            </button>
          </div>
        </div>
      </template>
    </modal>
  </Teleport>
</template>

<script>
export default {
  name: "NetworkGraph",
  components: {
    Side,
    NodeStats,
    LinkStats,
    PingallResults,
    ControllerForm,
    TopologyForm,
  },
  data() {
    return {
      hosts: {},
      switches: {},
      controllers: {},
      nats: {},
      routers: {},
      links: [],
      nodes: new DataSet(),
      edges: new DataSet(),
      portLabelNodes: {},
      portLabelListeners: null,
      addEdgeMode: false,
      networkStarted: false,
      networkCommandInFlight: false,
      runMenuOpen: false,
      toolsMenuOpen: false,
      viewMenuOpen: false,
      mininetConnected: true,
      healthTimer: null,
      pingallRunning: false,
      iperfBusy: false,
      iperfError: "",
      iperfResult: null,
      iperfForm: {
        client: "",
        server: "",
        l4_type: "TCP",
        seconds: 5,
        udp_bw: "",
        fmt: "",
        port: "",
      },
      snifferActive: false,
      hostsHidden: false,
      controllersHidden: false,
      sidebarCollapsed: false,
      webshellMinimized: false,
      showModal: false,
      modalHeader: "",
      modalOption: null,
      modalData: {},
      linkModalEdgeId: null,
      helpTab: "welcome",
      controllerFormPreset: null,
      controllerFormData: null,
      ryuApps: [],
      webshellView: null,
      webshellFocusId: null,
      webshellActiveView: null,
      terminalSessions: [],
      terminalSessionCounters: {},
      contextMenu: {
        visible: false,
        x: 0,
        y: 0,
        nodeId: null,
      },
      fileMenuOpen: false,
      helpMenuOpen: false,
      boundHandleGlobalClick: null,
      frontendVersion: frontendPackage?.version || "unknown",
      backendVersion: "unknown",
      mininetVersion: "unknown",
      selectionBox: {
        active: false,
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        append: false,
      },
      boundSelectionMouseDown: null,
      boundSelectionMouseMove: null,
      boundSelectionMouseUp: null,
      panState: {
        active: false,
        moved: false,
        startX: 0,
        startY: 0,
        startViewX: 0,
        startViewY: 0,
        scale: 1,
      },
      boundPanMouseDown: null,
      boundPanMouseMove: null,
      boundPanMouseUp: null,
      boundContextMenu: null,
      settings: {
      showHosts: true,
      showControllers: true,
      showSpecialSwitches: true,
      showSpecialControllers: true,
      showHostIp: false,
      showSwitchDpids: false,
      showPortLabels: false,
        openaiApiKey: "",
        linkOptions: {
          bw: "",
          delay: "",
          jitter: "",
          loss: "",
          max_queue_size: "",
          use_htb: false,
        },
      },
    };
  },
  computed: {
    network() {
      console.log("computed ran again");
      return this.computeNetwork();
    },
    networkCounts() {
      return {
        hosts: Object.keys(this.hosts || {}).length,
        controllers: Object.keys(this.controllers || {}).length,
        switches: Object.keys(this.switches || {}).length,
      };
    },
    networkStateIndicator() {
      if (this.networkCommandInFlight) return "network-state--pending";
      return this.networkStarted ? "network-state--started" : "network-state--stopped";
    },
    llmHandlers() {
      return {
        createHost: this.llmCreateHost,
        createSwitch: this.llmCreateSwitch,
        createController: this.llmCreateController,
        createLink: this.llmCreateLink,
        associateSwitch: this.llmAssociateSwitch,
        getTopology: this.llmGetTopology,
        runCommand: this.llmRunCommand,
        deleteNode: this.llmDeleteNode,
      };
    },
    selectionRectStyle() {
      const left = Math.min(this.selectionBox.startX, this.selectionBox.endX);
      const top = Math.min(this.selectionBox.startY, this.selectionBox.endY);
      const width = Math.abs(this.selectionBox.endX - this.selectionBox.startX);
      const height = Math.abs(this.selectionBox.endY - this.selectionBox.startY);
      return {
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        height: `${height}px`,
      };
    },
  },
  async mounted() {
    this.loadSettings();
    await this.syncSnifferState();
    this.snifferStateTimer = setInterval(() => this.syncSnifferState(), 5000);
    await this.loadRyuApps();
    this.setupNetwork();
    this.bindSelectionEvents();
    this.bindTopbarEvents();
    this.loadVersions();
    await this.refreshBackendHealth();
    this.healthTimer = setInterval(() => this.refreshBackendHealth(), 2000);
  },
  beforeUnmount() {
    if (this.snifferStateTimer) clearInterval(this.snifferStateTimer);
    this.unbindSelectionEvents();
    this.unbindTopbarEvents();
    if (this.healthTimer) clearInterval(this.healthTimer);
  },
  methods: {
    switchImageForType(type) {
      const key = (type || "ovskernel").toLowerCase();
      if (key === "user") return switchUserImg;
      if (key === "ovs") return switchOvsImg;
      if (key === "ovsbridge") return switchOvsBridgeImg;
      if (key === "ovskernel") return switchImg;
      return switchImg;
    },
    async loadVersions() {
      const backendInfo = await getBackendVersion();
      if (!backendInfo) return;
      if (backendInfo.version) this.backendVersion = backendInfo.version;
      if (backendInfo.mininet_version) this.mininetVersion = backendInfo.mininet_version;
    },
    async loadRyuApps() {
      this.ryuApps = await getRyuApps();
    },
    bindTopbarEvents() {
      if (!this.boundHandleGlobalClick) {
        this.boundHandleGlobalClick = this.handleGlobalClick.bind(this);
      }
      document.addEventListener("click", this.boundHandleGlobalClick);
    },
    unbindTopbarEvents() {
      if (this.boundHandleGlobalClick) {
        document.removeEventListener("click", this.boundHandleGlobalClick);
      }
    },
    handleGlobalClick(event) {
      const topbar = this.$refs.topbar;
      if (!topbar) return;
      if (this.fileMenuOpen && !topbar.contains(event.target)) {
        this.fileMenuOpen = false;
      }
      if (this.helpMenuOpen && !topbar.contains(event.target)) {
        this.helpMenuOpen = false;
      }
      if (this.runMenuOpen && !topbar.contains(event.target)) {
        this.runMenuOpen = false;
      }
      if (this.toolsMenuOpen && !topbar.contains(event.target)) {
        this.toolsMenuOpen = false;
      }
      if (this.viewMenuOpen && !topbar.contains(event.target)) {
        this.viewMenuOpen = false;
      }
    },
    toggleFileMenu() {
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      this.fileMenuOpen = !this.fileMenuOpen;
    },
    toggleHelpMenu() {
      this.fileMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      this.helpMenuOpen = !this.helpMenuOpen;
    },
    toggleToolsMenu() {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.viewMenuOpen = false;
      this.toolsMenuOpen = !this.toolsMenuOpen;
    },
    toggleViewMenu() {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = !this.viewMenuOpen;
    },
    closeFileMenu() {
      this.fileMenuOpen = false;
    },
    closeHelpMenu() {
      this.helpMenuOpen = false;
    },
    closeToolsMenu() {
      this.toolsMenuOpen = false;
    },
    closeViewMenu() {
      this.viewMenuOpen = false;
    },
    toggleRunMenu() {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      this.runMenuOpen = !this.runMenuOpen;
    },
    closeRunMenu() {
      this.runMenuOpen = false;
    },
    async handleStartNetwork() {
      this.closeRunMenu();
      if (this.networkCommandInFlight || this.networkStarted) return;
      this.networkCommandInFlight = true;
      try {
        const started = await requestStartNetwork();
        if (started) {
          this.networkStarted = true;
        }
      } finally {
        this.networkCommandInFlight = false;
        await this.refreshBackendHealth();
      }
    },
    async handleStopNetwork() {
      this.closeRunMenu();
      if (this.networkCommandInFlight || !this.networkStarted) return;
      this.networkCommandInFlight = true;
      try {
        const stopped = await requestStopNetwork();
        if (stopped) {
          this.snifferActive = false;
          this.networkStarted = false;
          await this.setupNetwork();
        }
      } finally {
        this.networkCommandInFlight = false;
        await this.refreshBackendHealth();
      }
    },
    async handleRestartNetwork() {
      this.closeRunMenu();
      if (this.networkCommandInFlight) return;
      this.networkCommandInFlight = true;
      try {
        const stopped = await requestStopNetwork();
        if (stopped) {
          this.snifferActive = false;
          this.networkStarted = false;
        }
        const restarted = await requestStartNetwork();
        if (restarted) {
          this.networkStarted = true;
          await this.setupNetwork();
        }
      } finally {
        this.networkCommandInFlight = false;
        await this.refreshBackendHealth();
      }
    },
    handleNewTopology() {
      this.closeFileMenu();
      this.showResetConfirmModal();
    },
    handleOpenTopology() {
      this.closeFileMenu();
      this.openFileDialog();
    },
    handleSaveTopology() {
      this.closeFileMenu();
      this.saveTopologyAs();
    },
    handleExportScript() {
      this.closeFileMenu();
      this.exportMininetScript();
    },
    handleExportSniffer() {
      this.closeFileMenu();
      this.exportSniffer();
    },
    handleExportPng() {
      this.closeFileMenu();
      this.exportTopologyAsPng();
    },
    handleExportAddressingPlan() {
      this.closeFileMenu();
      this.exportAddressingPlan();
    },
    handleOpenSettings() {
      this.closeFileMenu();
      this.showSettingsModal();
    },
    handleRunIperf() {
      this.closeToolsMenu();
      this.showIperfModal();
    },
    handleRunPingall() {
      this.closeToolsMenu();
      this.showPingallModal();
    },
    handleGenerateTopology() {
      this.closeToolsMenu();
      this.showTopologyFormModal();
    },
    async handleStartSniffer() {
      this.closeToolsMenu();
      if (this.snifferActive) return;
      await this.toggleSniffer();
    },
    async handleStopSniffer() {
      this.closeToolsMenu();
      if (!this.snifferActive) return;
      await this.toggleSniffer();
    },
    handleCollapseAllViews() {
      this.closeViewMenu();
      this.sidebarCollapsed = true;
      this.webshellMinimized = true;
    },
    handleExpandAllViews() {
      this.closeViewMenu();
      this.sidebarCollapsed = false;
      this.webshellMinimized = false;
    },
    handleOpenUsage() {
      this.closeHelpMenu();
      this.modalHeader = "Usage";
      this.modalOption = "usage";
      this.modalData = null;
      this.helpTab = "welcome";
      this.showModal = true;
    },
    handleOpenDocumentation() {
      this.closeHelpMenu();
      window.open("https://github.com/latarc/mininet-gui", "_blank", "noopener,noreferrer");
    },
    handleOpenAbout() {
      this.closeHelpMenu();
      this.modalHeader = "About";
      this.modalOption = "about";
      this.modalData = null;
      this.showModal = true;
    },
    openFileDialog() {
      this.$refs.topologyFileInput?.click();
    },
    handleFileUpload(event) {
      const file = event.target.files?.[0];
      if (file) {
        this.importTopology(file);
      }
      if (event.target) event.target.value = "";
    },
    bindSelectionEvents() {
      const graphEl = this.$refs.graphWrapper;
      if (!graphEl) return;
      if (!this.boundSelectionMouseDown) {
        this.boundSelectionMouseDown = this.handleSelectionMouseDown.bind(this);
        this.boundSelectionMouseMove = this.handleSelectionMouseMove.bind(this);
        this.boundSelectionMouseUp = this.handleSelectionMouseUp.bind(this);
      }
      graphEl.addEventListener("mousedown", this.boundSelectionMouseDown);
      if (!this.boundPanMouseDown) {
        this.boundPanMouseDown = this.handlePanMouseDown.bind(this);
        this.boundPanMouseMove = this.handlePanMouseMove.bind(this);
        this.boundPanMouseUp = this.handlePanMouseUp.bind(this);
        this.boundContextMenu = this.handleContextMenu.bind(this);
      }
      graphEl.addEventListener("mousedown", this.boundPanMouseDown);
      graphEl.addEventListener("contextmenu", this.boundContextMenu);
    },
    unbindSelectionEvents() {
      const graphEl = this.$refs.graphWrapper;
      if (graphEl) {
        graphEl.removeEventListener("mousedown", this.boundSelectionMouseDown);
        graphEl.removeEventListener("mousedown", this.boundPanMouseDown);
        graphEl.removeEventListener("contextmenu", this.boundContextMenu);
      }
      window.removeEventListener("mousemove", this.boundSelectionMouseMove);
      window.removeEventListener("mouseup", this.boundSelectionMouseUp);
      window.removeEventListener("mousemove", this.boundPanMouseMove);
      window.removeEventListener("mouseup", this.boundPanMouseUp);
    },
    handleSelectionMouseDown(event) {
      if (event.button !== 0) return;
      if (this.addEdgeMode) return;
      if (!this.network || !this.$refs.graphWrapper) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const localX = event.clientX - rect.left;
      const localY = event.clientY - rect.top;
      const hitNode = this.network.getNodeAt({ x: localX, y: localY });
      if (hitNode) return;
      event.preventDefault();
      this.hideContextMenu();
      this.selectionBox = {
        active: true,
        startX: localX,
        startY: localY,
        endX: localX,
        endY: localY,
        append: event.ctrlKey || event.metaKey,
      };
      window.addEventListener("mousemove", this.boundSelectionMouseMove);
      window.addEventListener("mouseup", this.boundSelectionMouseUp);
    },
    handlePanMouseDown(event) {
      if (event.button !== 1 && event.button !== 2) return;
      if (!this.network || !this.$refs.graphWrapper) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      this.panState = {
        active: true,
        moved: false,
        startX: event.clientX - rect.left,
        startY: event.clientY - rect.top,
        startViewX: this.network.getViewPosition().x,
        startViewY: this.network.getViewPosition().y,
        scale: this.network.getScale(),
      };
      window.addEventListener("mousemove", this.boundPanMouseMove);
      window.addEventListener("mouseup", this.boundPanMouseUp);
    },
    handlePanMouseMove(event) {
      if (!this.panState.active || !this.$refs.graphWrapper || !this.network) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const currentX = event.clientX - rect.left;
      const currentY = event.clientY - rect.top;
      const dx = currentX - this.panState.startX;
      const dy = currentY - this.panState.startY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
        this.panState.moved = true;
      }
      if (this.panState.moved) {
        event.preventDefault();
        const scale = this.panState.scale || this.network.getScale();
        this.network.moveTo({
          position: {
            x: this.panState.startViewX - dx / scale,
            y: this.panState.startViewY - dy / scale,
          },
          scale,
          animation: false,
        });
      }
    },
    handlePanMouseUp() {
      if (!this.panState.active) return;
      window.removeEventListener("mousemove", this.boundPanMouseMove);
      window.removeEventListener("mouseup", this.boundPanMouseUp);
      this.panState.active = false;
    },
    handleContextMenu(event) {
      if (this.panState.moved) {
        event.preventDefault();
        this.hideContextMenu();
      }
    },
    handleSelectionMouseMove(event) {
      if (!this.selectionBox.active || !this.$refs.graphWrapper) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const localX = event.clientX - rect.left;
      const localY = event.clientY - rect.top;
      this.selectionBox.endX = localX;
      this.selectionBox.endY = localY;
    },
    handleSelectionMouseUp(event) {
      if (!this.selectionBox.active) return;
      window.removeEventListener("mousemove", this.boundSelectionMouseMove);
      window.removeEventListener("mouseup", this.boundSelectionMouseUp);
      if (!this.$refs.graphWrapper || !this.network) {
        this.selectionBox.active = false;
        return;
      }
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const localX = event.clientX - rect.left;
      const localY = event.clientY - rect.top;
      this.selectionBox.endX = localX;
      this.selectionBox.endY = localY;
      this.finalizeSelection();
    },
    finalizeSelection() {
      const left = Math.min(this.selectionBox.startX, this.selectionBox.endX);
      const top = Math.min(this.selectionBox.startY, this.selectionBox.endY);
      const width = Math.abs(this.selectionBox.endX - this.selectionBox.startX);
      const height = Math.abs(this.selectionBox.endY - this.selectionBox.startY);
      const minDrag = 4;
      if (width < minDrag && height < minDrag) {
        this.selectionBox.active = false;
        return;
      }
      const topLeft = this.network.DOMtoCanvas({ x: left, y: top });
      const bottomRight = this.network.DOMtoCanvas({ x: left + width, y: top + height });
      const rectCanvas = {
        left: Math.min(topLeft.x, bottomRight.x),
        right: Math.max(topLeft.x, bottomRight.x),
        top: Math.min(topLeft.y, bottomRight.y),
        bottom: Math.max(topLeft.y, bottomRight.y),
      };
      const selected = [];
      const nodes = this.nodes?.get ? this.nodes.get() : [];
      nodes.forEach((node) => {
        if (node?.type === "portLabel") {
          return;
        }
        const box = this.network.getBoundingBox(node.id);
        if (
          box.right >= rectCanvas.left &&
          box.left <= rectCanvas.right &&
          box.bottom >= rectCanvas.top &&
          box.top <= rectCanvas.bottom
        ) {
          selected.push(node.id);
        }
      });
      if (this.selectionBox.append) {
        const current = this.network.getSelectedNodes();
        const merged = new Set([...current, ...selected]);
        this.network.selectNodes([...merged], true);
      } else if (selected.length) {
        this.network.selectNodes(selected, true);
      } else {
        this.network.unselectAll();
      }
      this.selectionBox.active = false;
    },
    loadSettings() {
      try {
        const raw = localStorage.getItem("mininetGuiSettings");
        if (raw) {
          const parsed = JSON.parse(raw);
          this.settings = { ...this.settings, ...parsed };
        }
      } catch (error) {
        console.warn("Failed to load settings", error);
      }
      this.applyVisibilitySettings();
      this.applyPortLabels();
    },
    persistSettings() {
      try {
        localStorage.setItem("mininetGuiSettings", JSON.stringify(this.settings));
      } catch (error) {
        console.warn("Failed to persist settings", error);
      }
      this.applyVisibilitySettings();
      this.applyHostLabels();
      this.applySwitchLabels();
      this.applyPortLabels();
    },
    handleShowHostsSetting() {
      this.applyHostsVisibility();
      this.persistSettings();
    },
    handleShowControllersSetting() {
      this.applyControllersVisibility();
      this.persistSettings();
    },
    getLinkOptionsPayload() {
      const opts = this.settings.linkOptions || {};
      const payload = {};
      if (opts.bw !== "" && opts.bw !== null && opts.bw !== undefined) payload.bw = Number(opts.bw);
      if (opts.delay !== "" && opts.delay !== null && opts.delay !== undefined) payload.delay = Number(opts.delay);
      if (opts.jitter !== "" && opts.jitter !== null && opts.jitter !== undefined) payload.jitter = Number(opts.jitter);
      if (opts.loss !== "" && opts.loss !== null && opts.loss !== undefined) payload.loss = Number(opts.loss);
      if (opts.max_queue_size !== "" && opts.max_queue_size !== null && opts.max_queue_size !== undefined) {
        payload.max_queue_size = Number(opts.max_queue_size);
      }
      if (opts.use_htb) payload.use_htb = true;
      return Object.keys(payload).length ? payload : null;
    },
    formatLinkTitle(options) {
      if (!options) return "No link attributes";
      const parts = [];
      if (options.bw !== undefined) parts.push(`bw: ${options.bw} Mbps`);
      if (options.delay !== undefined) parts.push(`delay: ${options.delay} ms`);
      if (options.jitter !== undefined) parts.push(`jitter: ${options.jitter} ms`);
      if (options.loss !== undefined) parts.push(`loss: ${options.loss} %`);
      if (options.max_queue_size !== undefined) parts.push(`queue: ${options.max_queue_size}`);
      if (options.use_htb) parts.push("htb: true");
      return parts.length ? parts.join(" | ") : "No link attributes";
    },
    formatPortLabel(intfs) {
      if (!intfs?.from || !intfs?.to) return "";
      return `${intfs.from} ↔ ${intfs.to}`;
    },
    getPortLabelTexts(intfs) {
      if (!intfs) return null;
      const fromLabel = intfs.from || "";
      const toLabel = intfs.to || "";
      if (!fromLabel && !toLabel) return null;
      return { fromLabel, toLabel };
    },
    hostLabel(host) {
      if (!host) return "";
      if (this.settings.showHostIp && host.ip) {
        return `${host.name}\n${host.ip}`;
      }
      return `${host.name}`;
    },
    switchLabel(sw) {
      if (!sw) return "";
      if (this.settings.showSwitchDpids) {
        const num = Number(String(sw.id || sw.name).replace(/^s/, ""));
        if (!Number.isNaN(num)) {
          return `${sw.name} <${this.intToDpid(num)}>`;
        }
      }
      return `${sw.name}`;
    },
    controllerLabel(ctl) {
      if (!ctl) return "";
      const controllerType = (ctl.controller_type || "").toLowerCase();
      const isRyu = controllerType === "ryu";
      const isRemote = ctl.remote || controllerType === "remote";
      if (isRemote || isRyu) {
        const targetParts = [];
        if (ctl.ip) targetParts.push(ctl.ip);
        if (ctl.port) targetParts.push(String(ctl.port));
        const target = targetParts.length ? ` <${targetParts.join(":")}>` : "";
        const parts = [`${ctl.name}${target}`];
        if (isRyu && ctl.ryu_app) {
          parts.push(`[ryu:${ctl.ryu_app}]`);
        }
        return parts.join(" ");
      }
      return `${ctl.name}`;
    },
    controllerColor() {
      return {
        background: "#252526",
        border: "#00000000",
        highlight: { background: "#848484", border: "#848484" },
      };
    },
    controllerImageForColor(colorCode) {
      const fill = colorCode || "#ffffff";
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36"><path d="M26.5,2h-17C8.7,2,8,2.7,8,3.5V34h20V3.5C28,2.7,27.3,2,26.5,2z M18,30.5c-1.5,0-2.8-1.2-2.8-2.8S16.5,25,18,25s2.8,1.2,2.8,2.8S19.5,30.5,18,30.5z M23,22.6H13V21h10V22.6z M24,11.6H12V10h12V11.6z M24,7.6H12V6h12V7.6z" fill="${fill}"/><circle cx="18" cy="27.8" r="1.2" fill="${fill}"/></svg>`;
      return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
    },
    applyHostLabels() {
      Object.values(this.hosts || {}).forEach((host) => {
        const label = this.hostLabel(host);
        host.label = label;
        this.nodes.update({ id: host.id, label });
      });
    },
    applySwitchLabels() {
      Object.values(this.switches || {}).forEach((sw) => {
        const label = this.switchLabel(sw);
        sw.label = label;
        this.nodes.update({ id: sw.id, label });
      });
    },
    applyHostsVisibility() {
      this.hostsHidden = !this.settings.showHosts;
      if (!this.nodes || !this.nodes.forEach) return;
      this.nodes.forEach((node) => {
        if (node.type === "host") {
          node.hidden = this.hostsHidden;
          this.nodes.updateOnly(node);
        }
      });
    },
    applyControllersVisibility() {
      this.controllersHidden = !this.settings.showControllers;
      if (!this.nodes || !this.nodes.forEach) return;
      this.nodes.forEach((node) => {
        if (node.type === "controller") {
          node.hidden = this.controllersHidden;
          this.nodes.updateOnly(node);
        }
      });
    },
    applyVisibilitySettings() {
      this.applyHostsVisibility();
      this.applyControllersVisibility();
    },
    applyPortLabels() {
      if (!this.edges || !this.edges.forEach || !this.nodes) return;
      const showLabels = !!this.settings.showPortLabels;
      if (!showLabels) {
        this.edges.forEach((edge) => {
          this.edges.updateOnly({ id: edge.id, label: "" });
        });
        this.clearAllPortLabelNodes();
        return;
      }
      this.edges.forEach((edge) => {
        this.edges.updateOnly({ id: edge.id, label: "" });
        this.ensurePortLabelNodes(edge);
      });
      this.updateAllPortLabelPositions();
    },
    bindPortLabelListeners() {
      if (!this.edges || !this.edges.on) return;
      if (this.portLabelListeners?.dataset && this.portLabelListeners?.dataset.off) {
        this.portLabelListeners.dataset.off("add", this.portLabelListeners.onAdd);
        this.portLabelListeners.dataset.off("update", this.portLabelListeners.onUpdate);
        this.portLabelListeners.dataset.off("remove", this.portLabelListeners.onRemove);
      }
      const onAdd = (event) => {
        if (!this.settings.showPortLabels) return;
        event.items.forEach((id) => {
          const edge = this.edges.get(id);
          if (edge) this.ensurePortLabelNodes(edge);
        });
      };
      const onUpdate = (event) => {
        if (!this.settings.showPortLabels) return;
        event.items.forEach((id) => {
          const edge = this.edges.get(id);
          if (edge) this.ensurePortLabelNodes(edge);
        });
      };
      const onRemove = (event) => {
        event.items.forEach((id) => this.removePortLabelNodes(id));
      };
      this.edges.on("add", onAdd);
      this.edges.on("update", onUpdate);
      this.edges.on("remove", onRemove);
      this.portLabelListeners = { dataset: this.edges, onAdd, onUpdate, onRemove };
    },
    clearAllPortLabelNodes() {
      if (!this.portLabelNodes || !this.nodes) return;
      Object.keys(this.portLabelNodes).forEach((edgeId) => this.removePortLabelNodes(edgeId));
      this.portLabelNodes = {};
    },
    removePortLabelNodes(edgeId) {
      if (!this.portLabelNodes?.[edgeId] || !this.nodes) return;
      const { fromId, toId } = this.portLabelNodes[edgeId];
      this.nodes.remove([fromId, toId]);
      delete this.portLabelNodes[edgeId];
    },
    ensurePortLabelNodes(edge) {
      if (!edge || !edge.id || !this.nodes) return;
      const texts = this.getPortLabelTexts(edge.intfs);
      if (!texts || !this.settings.showPortLabels) {
        this.removePortLabelNodes(edge.id);
        return;
      }
      const fromId = `port-label-from-${edge.id}`;
      const toId = `port-label-to-${edge.id}`;
      const labelNodes = this.portLabelNodes[edge.id] || { fromId, toId };
      const baseNode = {
        type: "portLabel",
        shape: "text",
        selectable: false,
        physics: false,
        fixed: true,
        hidden: false,
        font: {
          size: 12,
          color: "#e6e6e6",
          face: "Fira Sans",
        },
      };
      if (!this.nodes.get(fromId)) {
        this.nodes.add({ id: fromId, label: texts.fromLabel, ...baseNode });
      } else {
        this.nodes.update({ id: fromId, label: texts.fromLabel, hidden: false });
      }
      if (!this.nodes.get(toId)) {
        this.nodes.add({ id: toId, label: texts.toLabel, ...baseNode });
      } else {
        this.nodes.update({ id: toId, label: texts.toLabel, hidden: false });
      }
      this.portLabelNodes[edge.id] = labelNodes;
      this.updatePortLabelPositionsForEdge(edge);
    },
    updatePortLabelPositionsForEdge(edgeOrId) {
      if (!this.nodes || !this.network) return;
      const edge = typeof edgeOrId === "string" ? this.edges.get(edgeOrId) : edgeOrId;
      if (!edge?.from || !edge?.to) return;
      const labelNodes = this.portLabelNodes?.[edge.id];
      if (!labelNodes) return;
      const fromNode = this.network?.body?.nodes?.[edge.from];
      const toNode = this.network?.body?.nodes?.[edge.to];
      const fromX = fromNode?.x ?? this.nodes.get(edge.from)?.x;
      const fromY = fromNode?.y ?? this.nodes.get(edge.from)?.y;
      const toX = toNode?.x ?? this.nodes.get(edge.to)?.x;
      const toY = toNode?.y ?? this.nodes.get(edge.to)?.y;
      if (fromX === undefined || toX === undefined) return;
      const dx = toX - fromX;
      const dy = toY - fromY;
      const len = Math.hypot(dx, dy) || 1;
      const ux = dx / len;
      const uy = dy / len;
      const px = -uy;
      const py = ux;
      const offset = 26;
      const perp = 10;
      const fromPos = {
        x: fromX + ux * offset + px * perp,
        y: fromY + uy * offset + py * perp,
      };
      const toPos = {
        x: toX - ux * offset - px * perp,
        y: toY - uy * offset - py * perp,
      };
      this.nodes.update([
        { id: labelNodes.fromId, x: fromPos.x, y: fromPos.y },
        { id: labelNodes.toId, x: toPos.x, y: toPos.y },
      ]);
    },
    updatePortLabelPositionsForNode(nodeId) {
      if (!this.settings.showPortLabels || !this.network) return;
      const edges = this.network.getConnectedEdges(nodeId) || [];
      edges.forEach((edgeId) => this.updatePortLabelPositionsForEdge(edgeId));
    },
    updateAllPortLabelPositions() {
      if (!this.portLabelNodes) return;
      Object.keys(this.portLabelNodes).forEach((edgeId) => this.updatePortLabelPositionsForEdge(edgeId));
    },
    showSettingsModal() {
      this.closeAllActiveModes();
      this.modalHeader = "Settings";
      this.modalOption = "settings";
      this.showModal = true;
    },
    computeNetwork() {
      if (this.network)
        return this.network;
      return new Network(this.$refs.graph, {nodes: this.nodes, edges: this.edges}, options);
    },
    async setupNetwork() {
      await this.refreshBackendHealth();
      this.hosts = await getHosts();
      this.switches = await getSwitches();
      this.controllers = await getControllers();
      this.nats = await getNats();
      this.routers = await getRouters();

      Object.values(this.hosts).map((host) => {
        host.shape = "circularImage";

        host.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        };
        host.image = hostImg;
        host.label = this.hostLabel(host);
        host.hidden = this.hostsHidden;
        return host;
      });

      Object.values(this.switches).map((sw) => {
        sw.shape = "circularImage";
        sw.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        };
        sw.image = this.switchImageForType(sw.switch_type);
        sw.label = this.switchLabel(sw);
        return sw;
      });

      Object.values(this.controllers).map((ctl) => {
        ctl.shape = "circularImage";
        ctl.colorCode = ctl.color || "#ffffff";
        ctl.color = this.controllerColor();
        ctl.image = this.controllerImageForColor(ctl.colorCode);
        ctl.label = this.controllerLabel(ctl);
        ctl.hidden = this.controllersHidden;
        return ctl;
      });

      Object.values(this.nats).map((nat) => {
        nat.shape = "circularImage";
        nat.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        };
        nat.image = natImg;
        nat.label = nat.name || nat.id;
        return nat;
      });

      Object.values(this.routers).map((router) => {
        router.shape = "circularImage";
        router.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        };
        router.image = routerImg;
        router.label = router.name || router.id;
        return router;
      });

      this.links = await getEdges();
      for (const link of this.links) {
        const options = link.options || null;
        const intfs = link.intfs || null;
        this.edges.add({
          from: link.from,
          to: link.to,
          color: this.networkStarted ? "#00aa00ff" : "#999999ff",
          title: this.formatLinkTitle(options),
          options,
          intfs,
        });
      }
      for (const sw in this.switches) {
        let ctl = this.switches[sw].controller;
        if (ctl)
          this.edges.add({
            from: sw,
            to: ctl,
            color: "#777788af",
            dashes: [10, 10]
          });
      }

      const nodes = new DataSet([
        ...Object.values(this.hosts),
        ...Object.values(this.switches),
        ...Object.values(this.controllers),
        ...Object.values(this.nats),
        ...Object.values(this.routers),
      ]);
      this.nodes = nodes;
      this.applyVisibilitySettings();
      this.selectInitialWebshell();
      this.bindPortLabelListeners();
      this.applyPortLabels();
      console.log("network inside mounted, before setup:", this.network);
      this.network.setOptions({
        manipulation: {
          enabled: false,
          addEdge: async (data, callback) => {
            if (data.from == data.to) {
              confirm("Cannot connect node to itself");
              return;
            }
            console.log("network", this.network);
            let from = this.nodes.get(data.from);
            let to = this.nodes.get(data.to);
            if (from.type === "controller" && to.type === "controller") {
                alert("cannot connect controller with controller");
                return;
            } else if (from.type === "host" && this.hostHasLink(from.id)) {
                alert("host already has a link");
                return;
            } else if (to.type === "host" && this.hostHasLink(to.id)) {
                alert("host already has a link");
                return;
            } else if (from.type === "controller" || to.type === "controller") {
                if (from.type === "host" || to.type === "host") {
                    alert("cannot associate host with controller");
                    return;
                }
                let [sw, ctl] = (from.type === "controller") ? [to, from] : [from, to];
                sw.controller = ctl.id;
                await assocSwitch(sw.id, ctl.id);
                data.color = {color: "#777788af"};
                data.dashes = [10, 10];
            } else {
              const options = this.getLinkOptionsPayload();
              let link = await deployLink(data.from, data.to, options);
              data.id = link.id;
              data.color = {color: this.networkStarted ? "#00aa00ff" : "#999999ff"};
              data.title = this.formatLinkTitle(options);
              data.options = options;
              data.intfs = link?.intfs || null;
            }
            callback(data);
            this.enterAddEdgeMode();
            if (this.settings.showPortLabels && data.intfs) {
              this.ensurePortLabelNodes(this.edges.get(data.id));
            }
          },
          deleteNode: async (data, callback) => {
            console.log("node deletion", data);
            let results = [];
            for (const nodeId of data.nodes) {
              try {
                await deleteNode(nodeId);
                results.push(nodeId);
              } catch (error) {
                console.log("error deleting node", nodeId, error);
              }
            }
            data.nodes = results;
            callback(data);
          },
          deleteEdge: async (data, callback) => {
            try {
              const results = [];
              for (const edge of data.edges) {
                  let link = this.edges.get(edge);
                  let src = this.nodes.get(link.from);
                  let dst = this.nodes.get(link.to);
                  console.log("src", src);
                  console.log("dst", dst);
                  if (src.type == "controller" || dst.type == "controller") {
                    await removeAssociation(link.from, link.to);
                  } else {
                    await deleteLink(link.from, link.to);
                  }
                  results.push(link.id);
              }
              console.log("All edges deleted:", results);
              data.edges = results;
              callback(data);
            } catch (error) {
              console.error("Error deleting edges:", error);
            }
          },
        },
      });
      this.network.on("doubleClick", async (event) => {
        if (event.nodes.length === 1) {
          this.showStatsModal(event.nodes[0]);
          return;
        }
        if (event.edges.length === 1) {
          this.showLinkModal(event.edges[0]);
        }
      });
      this.network.on("oncontext", (event) => {
        if (event?.event?.preventDefault) {
          event.event.preventDefault();
        }
        const pointer = event?.pointer?.DOM;
        const nodeId = pointer ? this.network.getNodeAt(pointer) : event?.nodes?.[0];
        if (!nodeId) {
          this.hideContextMenu();
          return;
        }
        this.network.unselectAll();
        this.network.selectNodes([nodeId], false);
        const clientX = event?.event?.clientX ?? 0;
        const clientY = event?.event?.clientY ?? 0;
        this.contextMenu = {
          visible: true,
          x: clientX,
          y: clientY,
          nodeId,
        };
      });
      this.network.on("click", () => {
        this.hideContextMenu();
      });
      this.network.on("dragEnd", async (event) => {
        this.handleNodeDragEnd(event);
      });
    },
    async refreshBackendHealth() {
      try {
        const health = await getHealthStatus();
        if (health) {
          this.mininetConnected = !!health.connected;
          this.networkStarted = !!health.network_started;
        } else {
          this.mininetConnected = false;
          this.networkStarted = false;
        }
      } catch (error) {
        console.warn("Could not refresh backend health", error);
        this.mininetConnected = false;
        this.networkStarted = false;
      }
      this.updateLinkColors();
    },
    updateLinkColors() {
      if (!this.edges?.forEach) return;
      const colorValue = this.networkStarted ? "#00aa00ff" : "#999999ff";
      const updates = [];
      this.edges.forEach((edge) => {
        if (edge?.dashes?.length) return;
        const currentColor = edge.color;
        const normalizedColor =
          typeof currentColor === "object" && currentColor !== null && "color" in currentColor
            ? { ...currentColor, color: colorValue }
            : colorValue;
        updates.push({ id: edge.id, color: normalizedColor });
      });
      if (updates.length) {
        this.edges.update(updates);
        if (this.network) {
          this.network.redraw();
        }
      }
    },
    selectInitialWebshell() {
      this.webshellFocusId = null;
      this.webshellView = "logs";
    },
    getLowestNodeId(ids) {
      return [...ids].sort(this.compareNodeIds)[0];
    },
    compareNodeIds(a, b) {
      const parse = (value) => {
        const match = String(value).match(/^([a-zA-Z]+)(\d+)$/);
        if (!match) return { prefix: String(value), num: Number.MAX_SAFE_INTEGER };
        return { prefix: match[1], num: Number(match[2]) };
      };
      const pa = parse(a);
      const pb = parse(b);
      if (pa.prefix === pb.prefix) return pa.num - pb.num;
      return pa.prefix.localeCompare(pb.prefix);
    },
    openWebshellForNode(nodeId) {
      if (!nodeId) return;
      const nextCount = (this.terminalSessionCounters[nodeId] || 0) + 1;
      this.terminalSessionCounters = {
        ...this.terminalSessionCounters,
        [nodeId]: nextCount,
      };
      const sessionId = `${nodeId}-${nextCount}-${Date.now()}`;
      const label = `${nodeId}(${nextCount})`;
      this.terminalSessions = [
        ...this.terminalSessions,
        { id: sessionId, nodeId, label },
      ];
      this.webshellView = "terminal";
      this.webshellFocusId = null;
      this.$nextTick(() => {
        this.webshellFocusId = sessionId;
      });
    },
    hideContextMenu() {
      if (!this.contextMenu.visible) return;
      this.contextMenu = {
        visible: false,
        x: 0,
        y: 0,
        nodeId: null,
      };
    },
    openWebshellFromMenu() {
      const nodeId = this.contextMenu.nodeId;
      this.hideContextMenu();
      this.openWebshellForNode(nodeId);
    },
    openNodeStatsFromMenu() {
      const nodeId = this.contextMenu.nodeId;
      this.hideContextMenu();
      if (nodeId && this.nodes.get(nodeId)?.type === "portLabel") return;
      if (nodeId) this.showStatsModal(nodeId);
    },
    handleCloseSession(sessionId) {
      this.terminalSessions = this.terminalSessions.filter(session => session.id !== sessionId);
    },
    handleWebshellViewChange(view) {
      this.webshellActiveView = view;
    },
    hostHasLink(hostId) {
      const edges = this.edges?.get ? this.edges.get() : [];
      return edges.some((edge) => edge.from === hostId || edge.to === hostId);
    },
    async createLinkBetween(fromId, toId) {
      const fromNode = this.nodes.get(fromId);
      const toNode = this.nodes.get(toId);
      if (!fromNode || !toNode) {
        throw new Error("Invalid node ids for link.");
      }
      const options = this.getLinkOptionsPayload();
      const link = await deployLink(fromId, toId, options);
      const [edgeId] = this.edges.add({
        from: fromId,
        to: toId,
        color: { color: this.networkStarted ? "#00aa00ff" : "#999999ff" },
        title: this.formatLinkTitle(options),
        options,
        intfs: link?.intfs || null,
      });
      if (this.settings.showPortLabels) {
        this.ensurePortLabelNodes(this.edges.get(edgeId));
      }
      return link;
    },
    async llmCreateHost({ nodes } = {}) {
      if (!Array.isArray(nodes) || nodes.length === 0) {
        throw new Error("nodes array is required.");
      }
      const created = [];
      for (const entry of nodes) {
        if (!Number.isFinite(entry?.x) || !Number.isFinite(entry?.y)) {
          throw new Error("Each node requires numeric x and y.");
        }
        const host = await this.createHost({ x: entry.x, y: entry.y });
        created.push(host.id);
      }
      return { ids: created };
    },
    async llmCreateSwitch({ nodes } = {}) {
      if (!Array.isArray(nodes) || nodes.length === 0) {
        throw new Error("nodes array is required.");
      }
      const created = [];
      for (const entry of nodes) {
        if (!Number.isFinite(entry?.x) || !Number.isFinite(entry?.y)) {
          throw new Error("Each node requires numeric x and y.");
        }
        const sw = await this.createSwitch({ x: entry.x, y: entry.y });
        created.push(sw.id);
      }
      return { ids: created };
    },
    async llmCreateController({ nodes } = {}) {
      if (!Array.isArray(nodes) || nodes.length === 0) {
        throw new Error("nodes array is required.");
      }
      const created = [];
      for (const entry of nodes) {
        if (!Number.isFinite(entry?.x) || !Number.isFinite(entry?.y)) {
          throw new Error("Each node requires numeric x and y.");
        }
        const remote = Boolean(entry?.remote);
        const ip = remote ? entry?.ip : null;
        const port = remote ? entry?.port : null;
        const controllerType = entry?.controller_type || (remote ? "remote" : "default");
        const ryuApp = controllerType === "ryu" ? entry?.ryu_app : null;
        await this.createController({ x: entry.x, y: entry.y }, remote, ip, port, controllerType, ryuApp);
        const lastId = Object.keys(this.controllers).sort(this.compareNodeIds).pop();
        if (lastId) created.push(lastId);
      }
      return { ids: created };
    },
    async llmCreateLink({ from, to } = {}) {
      if (!from || !to) throw new Error("from and to are required.");
      const link = await this.createLinkBetween(from, to);
      return { from: link.from ?? from, to: link.to ?? to };
    },
    async llmAssociateSwitch({ switch_id, controller_id } = {}) {
      if (!switch_id || !controller_id) throw new Error("switch_id and controller_id are required.");
      await assocSwitch(switch_id, controller_id);
      this.edges.add({
        from: switch_id,
        to: controller_id,
        color: { color: "#777788af" },
        dashes: [10, 10],
      });
      if (this.switches[switch_id]) {
        this.switches[switch_id].controller = controller_id;
      }
      return { ok: true };
    },
    async llmGetTopology() {
      const nodes = [
        ...Object.values(this.hosts || {}),
        ...Object.values(this.switches || {}),
        ...Object.values(this.controllers || {}),
      ].map((node) => ({
        id: node.id,
        type: node.type,
        name: node.name,
        label: node.label,
        ip: node.ip,
        controller: node.controller,
      }));
      const edges = (this.edges?.get ? this.edges.get() : []).map((edge) => ({
        from: edge.from,
        to: edge.to,
        title: edge.title,
        dashes: edge.dashes,
        color: edge.color,
      }));
      return { nodes, edges };
    },
    async llmRunCommand({ node_id, command } = {}) {
      if (!node_id || !command) throw new Error("node_id and command are required.");
      const wsUrl = `${import.meta.env.VITE_BACKEND_WS_URL}/api/mininet/terminal/${node_id}`;
      return await new Promise((resolve, reject) => {
        const ws = new WebSocket(wsUrl);
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error("Command timed out."));
        }, 4000);
        ws.onopen = () => {
          ws.send(command + "\n");
          setTimeout(() => {
            clearTimeout(timeout);
            ws.close();
            resolve({ ok: true });
          }, 300);
        };
        ws.onerror = () => {
          clearTimeout(timeout);
          reject(new Error("WebSocket error while running command."));
        };
      });
    },
    async llmDeleteNode({ node_id } = {}) {
      if (!node_id) throw new Error("node_id is required.");
      await deleteNode(node_id);
      this.nodes.remove(node_id);
      delete this.hosts[node_id];
      delete this.switches[node_id];
      delete this.controllers[node_id];
      delete this.nats[node_id];
      delete this.routers[node_id];
      return { deleted: node_id };
    },
    intToDpid (number) {
      return number.toString(16).padStart(16, '0').replace(/(..)(..)(..)(..)(..)(..)(..)(..)/, '$1:$2:$3:$4:$5:$6:$7:$8');
    },
    async createHost(position) {
      let hostId = Object.values(this.hosts).length + 1;
      while (`h${hostId}` in this.hosts) {
        hostId++;
      }
      let host = {
        id: `h${hostId}`,
        type: "host",
        name: `h${hostId}`,
        label: null,
        ip: `10.0.0.${hostId}/8`,
        mac: hostId.toString(16).toUpperCase().padStart(12, "0"),
        shape: "circularImage",
        color: {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        },
      };
      host.label = this.hostLabel(host);
      host.image = hostImg;
      host.hidden = !this.settings.showHosts;
      if (position) {
        host.x = position.x;
        host.y = position.y;
      }
      if (await deployHost(host)) {
        this.nodes.add(host);
        this.hosts[host.name] = host;
      } else {
        throw "Could not create host " + hostId;
      }
      return host;
    },
    async createRouter(position) {
      let routerId = Object.values(this.routers).length + 1;
      while (`r${routerId}` in this.routers) {
        routerId++;
      }
      const octet = 100 + routerId;
      let router = {
        id: `r${routerId}`,
        type: "router",
        name: `r${routerId}`,
        label: `r${routerId}`,
        ip: `10.0.0.${octet}/8`,
        mac: octet.toString(16).toUpperCase().padStart(12, "0"),
        shape: "circularImage",
        color: {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        },
      };
      router.image = routerImg;
      if (position) {
        router.x = position.x;
        router.y = position.y;
      }
      if (await deployRouter(router)) {
        this.nodes.add(router);
        this.routers[router.name] = router;
      } else {
        throw "Could not create router " + routerId;
      }
      return router;
    },
    async createNat(position) {
      let natId = Object.values(this.nats).length + 1;
      while (`nat${natId}` in this.nats) {
        natId++;
      }
      const octet = 200 + natId;
      let nat = {
        id: `nat${natId}`,
        type: "nat",
        name: `nat${natId}`,
        label: `nat${natId}`,
        ip: `10.0.0.${octet}/8`,
        mac: octet.toString(16).toUpperCase().padStart(12, "0"),
        shape: "circularImage",
        color: {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        },
      };
      nat.image = natImg;
      if (position) {
        nat.x = position.x;
        nat.y = position.y;
      }
      if (await deployNat(nat)) {
        this.nodes.add(nat);
        this.nats[nat.name] = nat;
      } else {
        throw "Could not create NAT " + natId;
      }
      return nat;
    },
    async createSwitch(switchData) {
      let swId = Object.values(this.switches).length + 1;
      while (`s${swId}` in this.switches) {
        swId++;
      }
      const switchType = switchData?.switch_type || "ovskernel";
      let sw = {
        id: `s${swId}`,
        type: "sw",
        name: `s${swId}`,
        label: switchData.label || null,
        ports: switchData.ports || 4,
        controller: null,
        switch_type: switchType,
        shape: "circularImage",
        color: {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#848484", border: "#848484" },
        },
      };
      sw.label = this.switchLabel(sw);
      sw.image = this.switchImageForType(sw.switch_type);
      if (switchData) {
        sw.x = switchData.x;
        sw.y = switchData.y;
      }
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
      } else {
        throw "Could not create sw " + swId;
      }
      if (switchData.controller && await assocSwitch(sw.id, switchData.controller)) {
        this.switches[sw.name].controller = switchData.controller;
        this.edges.add({
          from: sw.id,
          to: switchData.controller,
          color: {color: "#777788af"},
          dashes: [10, 10]
        });
      }
      return sw;
    },
    async showControllerFormModal(position, presetType = null) {
      this.modalHeader = "Controller Form";
      this.modalOption = "controllerForm";
      this.showModal = true;
      this.controllerFormPreset = presetType;
      this.controllerFormData = null;
      this.formData = null;

      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });

      console.log("GOT DATA:", this.formData);
      await this.createController(
        position,
        this.formData.type === "remote",
        this.formData.ip,
        this.formData.port,
        this.formData.type,
        this.formData.ryu_app,
        this.formData.color
      );
    },
    showControllerEditModal(controllerId) {
      const controller = this.controllers?.[controllerId] || (this.modalData?.id === controllerId ? this.modalData : null);
      if (!controller) return;
      this.modalHeader = `Edit Controller: ${controllerId}`;
      this.modalOption = "controllerForm";
      this.showModal = true;
      this.controllerFormPreset = null;
      this.controllerFormData = {
        ...controller,
        color: controller.colorCode || controller.color || "#ffffff",
      };
    },
    handleControllerFormSubmit(data) {
      this.formData = data;
      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }
      this.showModal = false;
    },
    async handleControllerFormUpdate(data) {
      if (!this.controllerFormData?.id) return;
      const controllerId = this.controllerFormData.id;
      const payload = {
        controller_type: data.type,
        remote: data.type === "remote",
        ip: data.ip,
        port: data.port,
        ryu_app: data.ryu_app,
        color: data.color,
      };
      const updated = await updateController(controllerId, payload);
      if (!updated) return;
      const existing = this.controllers[controllerId] || {};
      const colorCode = updated.color || data.color || existing.colorCode || "#ffffff";
      const merged = {
        ...existing,
        ...updated,
        colorCode,
        color: this.controllerColor(),
      };
      merged.label = this.controllerLabel(merged);
      merged.image = this.controllerImageForColor(colorCode);
      this.controllers[controllerId] = merged;
      this.nodes.update({
        id: controllerId,
        label: merged.label,
        ip: merged.ip,
        port: merged.port,
        ryu_app: merged.ryu_app,
        controller_type: merged.controller_type,
        color: merged.color,
        image: merged.image,
      });
      this.closeModal();
    },
    async createController(position, remote, ip, port, controllerType = "default", ryuApp = null, colorCode = null) {
      let ctlId = Object.values(this.controllers).length + 1;
      while (`c${ctlId}` in this.controllers) {
        ctlId++;
      }
      const isRyu = controllerType === "ryu";
      const effectiveIp = ip || (isRyu ? "127.0.0.1" : ip);
      const color = colorCode || "#ffffff";
      let ctl = {
        id: `c${ctlId}`,
        type: "controller",
        name: `c${ctlId}`,
        label: null,
        controller_type: controllerType,
        remote: remote,
        ip: effectiveIp,
        port: port,
        x: position.x,
        y: position.y,
        shape: "circularImage",
        color: this.controllerColor(),
        colorCode: color,
      };
      if (isRyu) ctl.ryu_app = ryuApp;
      ctl.label = this.controllerLabel(ctl);
      ctl.image = this.controllerImageForColor(color);
      ctl.hidden = !this.settings.showControllers;
      if (await deployController(ctl)) {
        this.nodes.add(ctl);
        this.controllers[ctl.name] = ctl;
      } else {
        throw "Could not create controller " + ctlId;
      }
    },
    handleDrop(event) {
      this.closeAllActiveModes();
      event.preventDefault();
      console.log("drop event triggered, text/plain", event.dataTransfer.getData("text/plain"));
      var data = event.dataTransfer.getData("text/plain");
      const rect = this.$refs.graph.getBoundingClientRect();
      const domPoint = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      if (data === "draggable-host") {
        this.createHost(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-router") {
        this.createRouter(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-switch") {
        this.createSwitch(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-switch-ovs") {
        this.createSwitch({
          ...this.network.DOMtoCanvas(domPoint),
          switch_type: "ovs",
        });
      } else if (data === "draggable-switch-ovsbridge") {
        this.createSwitch({
          ...this.network.DOMtoCanvas(domPoint),
          switch_type: "ovsbridge",
        });
      } else if (data === "draggable-switch-user") {
        this.createSwitch({
          ...this.network.DOMtoCanvas(domPoint),
          switch_type: "user",
        });
      } else if (data === "draggable-controller-default") {
        this.createController(
          this.network.DOMtoCanvas(domPoint),
          false,
          null,
          null,
          "default"
        );
      } else if (data === "draggable-controller-remote") {
        this.showControllerFormModal(
          this.network.DOMtoCanvas(domPoint),
          "remote"
        );
      } else if (data === "draggable-controller-ryu") {
        this.showControllerFormModal(
          this.network.DOMtoCanvas(domPoint),
          "ryu"
        );
      } else if (data === "draggable-controller-nox") {
        this.createController(
          this.network.DOMtoCanvas(domPoint),
          false,
          null,
          null,
          "nox"
        );
      } else if (data === "draggable-nat") {
        this.createNat(
          this.network.DOMtoCanvas(domPoint),
        );
      }
    },
    async handleNodeDragEnd(event) {
      event.nodes.forEach(async nodeId => {
        const nodeData = this.nodes.get(nodeId);
        if (nodeData?.type === "portLabel") return;
        let node = this.network.body.nodes[nodeId];
        await updateNodePosition(nodeId, [node.x, node.y]);
        this.updatePortLabelPositionsForNode(nodeId);
      });
    },
    enterAddEdgeMode() {
      this.addEdgeMode = true;
      this.network.addEdgeMode();
    },
    closeAddEdgeMode() {
      this.addEdgeMode = false;
      this.network.disableEditMode();
    },
    closeModal() {
      this.modalHeader = "";
      this.showModal = false;
      this.modalOption = null;
      this.modalData = null;
      this.linkModalEdgeId = null;
      this.controllerFormPreset = null;
      this.controllerFormData = null;
      this.formData = null;
      this.iperfError = "";
      this.iperfResult = null;
    },
    closeAllActiveModes() {
      this.closeAddEdgeMode();
      this.closeModal();
      this.hideContextMenu();
    },
    handleToggleAddEdgeMode() {
      console.log("addedgemode toggle");
      if (!this.addEdgeMode) {
        this.enterAddEdgeMode();
      } else {
        this.closeAddEdgeMode();
      }
    },
    toggleShowHosts() {
      this.settings.showHosts = !this.settings.showHosts;
      this.applyHostsVisibility();
      this.persistSettings();
    },
    toggleShowControllers () {
      this.settings.showControllers = !this.settings.showControllers;
      this.applyControllersVisibility();
      this.persistSettings();
    },
    async doDeleteSelected() {
      this.closeAllActiveModes();
      this.network.deleteSelected();
    },
    doSelectAll() {
      console.log("CTRL A PRESSED");
      this.closeAllActiveModes();
      const ids = this.nodes.getIds().filter((id) => this.nodes.get(id)?.type !== "portLabel");
      this.network.setSelection({nodes: ids});
    },
    async showPingallModal() {
      if (this.pingallRunning) return;
      this.closeAllActiveModes();
      this.pingallRunning = true;

      let pingallResults = await requestRunPingall();
      if (pingallResults && pingallResults.running) {
        this.pingallRunning = false;
        return;
      } else {
        this.modalHeader = "Pingall Results";
        this.modalOption = "pingall";
        this.modalData = pingallResults || null;
        this.showModal = true;
      }
      this.pingallRunning = false;
    },
    showIperfModal() {
      if (this.iperfBusy) return;
      this.closeAllActiveModes();
      const hostIds = Object.keys(this.hosts || {});
      this.iperfForm.client = hostIds[0] || "";
      this.iperfForm.server = hostIds[1] || "";
      this.iperfForm.l4_type = "TCP";
      this.iperfForm.seconds = 5;
      this.iperfForm.udp_bw = "";
      this.iperfForm.fmt = "";
      this.iperfForm.port = "";
      this.iperfError = "";
      this.iperfResult = null;
      this.modalHeader = "Run Iperf";
      this.modalOption = "iperf";
      this.showModal = true;
    },
    async runIperfTest() {
      if (!this.iperfForm.client || !this.iperfForm.server) return;
      if (this.iperfForm.client === this.iperfForm.server) {
        this.iperfError = "Client and server must be different hosts.";
        return;
      }
      this.closeModal();
      this.iperfBusy = true;
      this.iperfError = "";
      this.iperfResult = null;
      const payload = {
        client: this.iperfForm.client,
        server: this.iperfForm.server,
        l4_type: this.iperfForm.l4_type,
      };
      if (this.iperfForm.seconds) payload.seconds = Number(this.iperfForm.seconds);
      if (this.iperfForm.port) payload.port = Number(this.iperfForm.port);
      if (this.iperfForm.fmt) payload.fmt = this.iperfForm.fmt;
      if (this.iperfForm.l4_type === "UDP" && this.iperfForm.udp_bw) {
        payload.udp_bw = this.iperfForm.udp_bw;
      }
      const result = await runIperf(payload);
      if (result?.running) {
        this.iperfError = "Iperf already running.";
        this.iperfBusy = false;
        this.modalHeader = "Run Iperf";
        this.modalOption = "iperf";
        this.showModal = true;
        return;
      }
      if (!result) {
        this.iperfError = "Failed to run iperf.";
      } else {
        this.iperfResult = result;
      }
      this.iperfBusy = false;
      this.modalHeader = "Iperf Results";
      this.modalOption = "iperf";
      this.showModal = true;
    },
    formatIperfResult(result) {
      if (!result) return "";
      if (result.client && result.server) {
        return `Client: ${result.client}\nServer: ${result.server}`;
      }
      return JSON.stringify(result, null, 2);
    },
    async showStatsModal(nodeId) {
      this.closeAllActiveModes();
      this.modalHeader = `Node Info: ${nodeId}`;
      this.modalOption = "nodeStats";
      let nodeStats = await getNodeStats(nodeId);
      console.log("nodeStats", nodeStats);
      this.modalData = nodeStats || null;
      this.showModal = true;
    },
    showLinkModal(edgeId) {
      if (!edgeId) return;
      const link = this.edges.get(edgeId);
      if (!link?.from || !link?.to) return;
      const srcNode = this.nodes.get(link.from);
      const dstNode = this.nodes.get(link.to);
      if (srcNode?.type === "controller" || dstNode?.type === "controller") {
        return;
      }
      this.closeAllActiveModes();
      this.modalHeader = `Link Info: ${link.from} ↔ ${link.to}`;
      this.modalOption = "linkStats";
      this.modalData = {
        from: link.from,
        to: link.to,
        options: link.options || null,
      };
      this.linkModalEdgeId = edgeId;
      this.showModal = true;
    },
    handleLinkUpdated(options) {
      if (!this.linkModalEdgeId) return;
      this.edges.update({
        id: this.linkModalEdgeId,
        options,
        title: this.formatLinkTitle(options),
      });
      if (this.modalOption === "linkStats") {
        this.modalData = { ...this.modalData, options };
      }
    },
    handleHostUpdated(updatedHost) {
      if (!updatedHost?.id) return;
      const existing = this.hosts[updatedHost.id];
      if (existing) {
        existing.ip = updatedHost.ip;
        this.hosts[updatedHost.id] = existing;
        this.nodes.update({ id: updatedHost.id, ip: updatedHost.ip, label: this.hostLabel(existing) });
      }
      if (this.modalOption === "nodeStats") {
        this.modalData = updatedHost;
      }
    },
    async createSingleTopo(nDevices, controller) {
      let newSw = await this.createSwitch({x: 250, y: 150, controller: controller});
      for (var i=0; i<nDevices; i++) {
        let newHost = await this.createHost({x: 200+i*90, y: 300});
        let link = await deployLink(newSw.id, newHost.id);
        const [edgeId] = this.edges.add({
          from: newSw.id,
          to: newHost.id,
          color: this.networkStarted ? "#00aa00ff" : "#999999ff",
          intfs: link?.intfs || null,
        });
        if (this.settings.showPortLabels) {
          this.ensurePortLabelNodes(this.edges.get(edgeId));
        }
      }
    },
    async createLinearTopo(nDevices, nHosts, controller) {
      let prevSw = null;
      for (let i = 0; i < nDevices; i++) {
        let newSw = await this.createSwitch({ x: 250 + i * 90, y: 150, controller: controller});
        console.log("newSw", newSw);

        for (let j = 0; j < nHosts; j++) {
          let newHost = await this.createHost({ x: 200 + i * 90, y: 300 + j * 50 });
          console.log("newHost", newHost);

          const link = await deployLink(newSw.id, newHost.id);
          const [edgeId] = this.edges.add({
            from: newSw.id,
            to: newHost.id,
            color: this.networkStarted ? "#00aa00ff" : "#999999ff",
            intfs: link?.intfs || null,
          });
          if (this.settings.showPortLabels) {
            this.ensurePortLabelNodes(this.edges.get(edgeId));
          }
        }

        if (prevSw) {
          const link = await deployLink(newSw.id, prevSw.id);
          const [edgeId] = this.edges.add({
            from: newSw.id,
            to: prevSw.id,
            color: this.networkStarted ? "#00aa00ff" : "#999999ff",
            intfs: link?.intfs || null,
          });
          if (this.settings.showPortLabels) {
            this.ensurePortLabelNodes(this.edges.get(edgeId));
          }
        }
        prevSw = newSw;
      }
    },
    async createTreeTopo(depth, fanout, controller) {
      const nodes = [];
      const maxNodes = Math.pow(fanout, depth);
      for (let d = depth; d >= 0; d--) {
        const layer = [];
        const numNodes = Math.pow(fanout, d);
        for (let i = 0; i < numNodes; i++) {
          let x = (i + 0.5) * maxNodes * 100 / (numNodes || 1);
          let y = 150 + d * 150;
          let node;
          if (d === depth) {
            node = await this.createHost({ x, y });
            console.log("Created Host:", node);
          } else {
            node = await this.createSwitch({ x: x, y: y, controller: controller});
            console.log("Created Switch:", node);
            const startIndex = i * fanout;
            const endIndex = startIndex + fanout;
            for (let j = startIndex; j < endIndex && j < nodes[d + 1].length; j++) {
              const child = nodes[d + 1][j];
              const link = await deployLink(node.id, child.id);
              const [edgeId] = this.edges.add({
                from: node.id,
                to: child.id,
                color: this.networkStarted ? "#00aa00ff" : "#999999ff",
                intfs: link?.intfs || null,
              });
              if (this.settings.showPortLabels) {
                this.ensurePortLabelNodes(this.edges.get(edgeId));
              }
            }
          }
          layer.push(node);
        }
        nodes[d] = layer;
      }
    },
    async showTopologyFormModal() {
      this.modalHeader = "Create Topology";
      this.modalOption = "topologyForm";
      this.showModal = true;

      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });

      console.log("GOT DATA", this.formData);
      await this.handleCreateTopology(this.formData.type, this.formData.nDevices, this.formData.nLayers, this.formData.controller);
    },
    handleTopologyFormSubmit(data) {
      this.formData = data;
      console.log("FORM DATA", this.formData);

      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }
      this.showModal = false;
    },
    async handleCreateTopology(topologyType, nDevices, nLayers, controller){
      console.log("Received createTopology event with:", topologyType, "data", nDevices, nLayers);
      if (topologyType == "Single") {
        await this.createSingleTopo(nDevices, controller);
      } else if (topologyType == "Linear") {
        await this.createLinearTopo(nDevices, nLayers, controller);
      } else if (topologyType == "Tree") {
        await this.createTreeTopo(nLayers, nDevices, controller);
      }
    },
    async resetTopology() {
      if (await requestFullResetNetwork()) {
        this.snifferActive = false;
        console.log("Resetting topology");
        this.clearGraphState();
        await this.refreshBackendHealth();
      }
    },
    clearGraphState() {
      this.hosts = {};
      this.switches = {};
      this.controllers = {};
      this.nats = {};
      this.routers = {};
      this.links = [];
      this.nodes = new DataSet();
      this.edges = new DataSet();
      this.portLabelNodes = {};
      this.bindPortLabelListeners();
      if (this.network) {
        this.network.setData({ nodes: this.nodes, edges: this.edges });
        this.network.redraw();
      }
    },
    handleSidebarToggle(isActive) {
      this.sidebarCollapsed = !isActive;
    },
    handleWebshellMinimizeChange(isMinimized) {
      this.webshellMinimized = !!isMinimized;
    },
    async toggleSniffer() {
      try {
        if (this.snifferActive) {
          const response = await stopSniffer();
          this.snifferActive = !!response.active;
        } else {
          const response = await startSniffer();
          this.snifferActive = !!response.active;
        }
      } catch (error) {
        this.snifferActive = false;
      }
    },
    async syncSnifferState() {
      try {
        const state = await getSnifferState();
        this.snifferActive = !!state.active;
      } catch (error) {
        // keep previous state; backend may not be ready yet
      }
    },
    async exportSniffer() {
      try {
        const blob = await exportSnifferPcap();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "sniffer.pcap";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Failed to export sniffer", error);
      }
    },
    exportTopologyAsPng() {
      try {
        const canvas = this.$refs.graph?.querySelector?.("canvas");
        if (!canvas) return;
        const dataUrl = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.href = dataUrl;
        link.download = "topology.png";
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error("Failed to export topology PNG", error);
        alert("Failed to export topology PNG.");
      }
    },
    showResetConfirmModal() {
      this.modalHeader = "Reset Topology";
      this.modalOption = "confirmReset";
      this.modalData = null;
      this.showModal = true;
    },
    async confirmResetTopology() {
      await this.resetTopology();
      this.closeModal();
    },
    async exportTopology() {
      await requestExportNetwork();
    },
    async saveTopologyAs() {
      const payload = this.buildTopologyExportPayload();
      const jsonData = JSON.stringify(payload, null, 2);
      const fileName = "topology.json";

      if ("showSaveFilePicker" in window) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: fileName,
            types: [
              {
                description: "JSON",
                accept: { "application/json": [".json"] },
              },
            ],
          });
          const writable = await handle.createWritable();
          await writable.write(jsonData);
          await writable.close();
          return;
        } catch (error) {
          if (error?.name === "AbortError") return;
        }
      }

      const blob = new Blob([jsonData], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
    async exportMininetScript() {
      await requestExportMininetScript();
    },
    async exportAddressingPlan() {
      try {
        const plan = await getAddressingPlan();
        const createdAt = new Date().toLocaleString();
        const nodes = plan?.nodes || [];
        const doc = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
        doc.text("Addressing Plan", 40, 40);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        doc.text(`Created in Mininet GUI – ${createdAt}`, 40, 60);
        doc.text("Repository: https://github.com/latarc/mininet-gui", 40, 74);

        const body = [];
        nodes.forEach((node) => {
          if (!node.intfs || node.intfs.length === 0) {
            body.push([node.id, node.type, "-", "-", "-", "-"]);
            return;
          }
          node.intfs.forEach((intf, idx) => {
            const ipv4 = (intf.ipv4 || []).join("\n");
            const ipv6 = (intf.ipv6 || []).join("\n");
            const mac = intf.mac || "";
            const row = [
              idx === 0 ? node.id : "",
              idx === 0 ? node.type : "",
              intf.name,
              mac,
              ipv4 || "-",
              ipv6 || "-",
            ];
            body.push(row);
          });
        });

        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.text("Nodes", 40, 86);
        doc.setFont("helvetica", "normal");
        autoTable(doc, {
          startY: 90,
          head: [["Node", "Type", "Interface", "MAC", "IPv4", "IPv6"]],
          body,
          styles: { fontSize: 8, cellPadding: 3, valign: "top" },
          headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] },
        });

        const afterNodes = doc.lastAutoTable?.finalY ? doc.lastAutoTable.finalY + 24 : 120;
        const linkRows = [];
        const edges = this.edges?.get ? this.edges.get() : [];
        edges.forEach((edge) => {
          linkRows.push([
            edge.from,
            edge.to,
            edge.title || "-",
          ]);
        });

        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.text("Links", 40, afterNodes - 8);
        doc.setFont("helvetica", "normal");
        autoTable(doc, {
          startY: afterNodes,
          head: [["From", "To", "Attributes"]],
          body: linkRows.length ? linkRows : [["-", "-", "No links"]],
          styles: { fontSize: 8, cellPadding: 3, valign: "top" },
          headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] },
        });

        const canvas = this.$refs.graph?.querySelector?.("canvas");
        const imageData = canvas ? canvas.toDataURL("image/png") : null;
        if (imageData) {
          doc.addPage();
          doc.setFont("helvetica", "bold");
          doc.setFontSize(14);
          doc.text("Network Graph", 40, 40);
          const pageWidth = doc.internal.pageSize.getWidth();
          const pageHeight = doc.internal.pageSize.getHeight();
          const maxWidth = pageWidth - 80;
          const maxHeight = pageHeight - 120;
          const img = new Image();
          img.src = imageData;
          const imgRatio = img.width && img.height ? img.width / img.height : 1.6;
          let imgWidth = maxWidth;
          let imgHeight = imgWidth / imgRatio;
          if (imgHeight > maxHeight) {
            imgHeight = maxHeight;
            imgWidth = imgHeight * imgRatio;
          }
          const x = (pageWidth - imgWidth) / 2;
          const y = 60;
          doc.addImage(imageData, "PNG", x, y, imgWidth, imgHeight, undefined, "FAST");
        }

        doc.save("addressing-plan.pdf");
      } catch (error) {
        console.error("Failed to export addressing plan", error);
        alert("Failed to export addressing plan.");
      }
    },
    async importTopology(file) {
      await this.resetTopology();
      const data = await requestImportNetwork(file);
      await this.setupNetwork();
      this.network.setData({nodes: this.nodes, edges: this.edges});
      this.network.redraw();
    },
    buildTopologyExportPayload() {
      try {
        const nodes = this.nodes?.get ? this.nodes.get() : [];
        const edges = this.edges?.get ? this.edges.get() : [];
        const nodesExport = nodes
          .filter((node) => node?.type !== "portLabel")
          .map((node) => {
          if (node.type === "host") {
            return {
              id: node.id,
              type: "host",
              name: node.name,
              ip: node.ip,
              mac: node.mac,
              x: node.x,
              y: node.y,
            };
          }
          if (node.type === "router") {
            return {
              id: node.id,
              type: "router",
              name: node.name,
              ip: node.ip,
              mac: node.mac,
              x: node.x,
              y: node.y,
            };
          }
          if (node.type === "controller") {
            return {
              id: node.id,
              type: "controller",
              name: node.name,
              controller_type: node.controller_type ?? (node.remote ? "remote" : "default"),
              remote: node.remote ?? false,
              ip: node.ip ?? null,
              port: node.port ?? null,
              x: node.x,
              y: node.y,
            };
          }
          if (node.type === "nat") {
            return {
              id: node.id,
              type: "nat",
              name: node.name,
              label: node.label ?? node.name,
              ip: node.ip ?? null,
              mac: node.mac ?? null,
              x: node.x,
              y: node.y,
            };
          }
          return {
            id: node.id,
            type: "switch",
            name: node.name,
            dpid: node.dpid,
            ports: node.ports,
            controller: node.controller ?? null,
            switch_type: node.switch_type ?? "ovskernel",
            x: node.x,
            y: node.y,
          };
        });
        const edgesExport = edges.map((edge) => ({
          from: edge.from,
          to: edge.to,
          options: edge.options ?? null,
          title: edge.title ?? null,
        }));
        return { nodes: nodesExport, edges: edgesExport };
      } catch (error) {
        console.warn("Failed to build topology export payload", error);
        return { nodes: [], edges: [] };
      }
    },
  }
};
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  position: relative;
}

.topbar {
  height: 32px;
  background: #2b2b2b;
  color: #d4d4d4;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 12px;
  border-bottom: 1px solid #1f1f1f;
  position: relative;
  z-index: 6;
  font-size: 0.85rem;
}

.topbar-title {
  font-weight: 600;
  letter-spacing: 0.2px;
  margin-right: 8px;
}

.menu-bar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.menu-item-wrapper {
  position: relative;
}

.menu-item {
  background: transparent;
  border: none;
  color: inherit;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.menu-item:hover,
.menu-item.open {
  background: #3c3c3c;
}

.menu-item:disabled {
  color: #7a7a7a;
  cursor: default;
}

.menu-dropdown {
  position: absolute;
  top: 28px;
  left: 0;
  background: #2d2d2d;
  border: 1px solid #1f1f1f;
  border-radius: 6px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 240px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.35);
}

.menu-action {
  background: transparent;
  border: none;
  color: #d4d4d4;
  padding: 6px 10px;
  text-align: left;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.menu-action:hover {
  background: #3c3c3c;
}

.menu-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #d4d4d4;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.82rem;
  cursor: pointer;
}

.menu-checkbox:hover {
  background: #3c3c3c;
}

.menu-checkbox input {
  accent-color: #007acc;
}

.health-overlay {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 28px;
  background: rgba(5, 5, 5, 0.92);
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.health-overlay__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #1e1e1e;
  border: 1px solid #3a3a3a;
  border-radius: 12px;
  padding: 20px 28px;
  max-width: 360px;
  text-align: center;
  color: #dcdcdc;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
}

.health-overlay__retry {
  margin-top: 4px;
  width: auto;
}

.menu-separator {
  height: 1px;
  margin: 4px 0;
  background: #444;
}

.help-modal__tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.help-modal__tabs button {
  background: #2d2d2d;
  border: 1px solid #444;
  color: #d4d4d4;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.help-modal__tabs button.active {
  background: #007acc;
  border-color: #007acc;
}

.menu-file-input {
  display: none;
}

.status-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 28px;
  background: #1d1d1d;
  border-top: 1px solid #2f2f2f;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 16px;
  z-index: 7;
  font-size: 0.8rem;
  color: #d4d4d4;
}

.status-bar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background-color: #9b9b9b;
}

.status-dot--started {
  background-color: #61efb5;
}

.status-dot--stopped {
  background-color: #9b9b9b;
}

.status-bar__text {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  line-height: 1;
  font-size: 0.7rem;
}

.status-bar__primary {
  font-weight: 600;
}

.status-bar__version {
  color: #a2a2a2;
}

.status-bar__counts {
  color: #d4d4d4;
  font-weight: 500;
}

.status-bar__network {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #d4d4d4;
}

.network-state-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background-color: #9b9b9b;
}

.network-state--started {
  background-color: #61efb5;
}

.network-state--stopped {
  background-color: #f06666;
}

.network-state--pending {
  background-color: #f5d76a;
}

.layout {
  display: flex;
  height: calc(100vh - 32px);
  overflow: hidden;
  width: 100%;
  --sidebar-width: 220px;
}

.layout.sidebar-collapsed {
  --sidebar-width: 64px;
}

.side-wrapper {
  padding: 8px;
  display: flex;
  flex-shrink: 0;
  width: calc(var(--sidebar-width) + 16px);
  min-width: calc(var(--sidebar-width) + 16px);
  max-width: calc(var(--sidebar-width) + 16px);
}

  .main-content {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    min-width: 0;
    position: relative;
    z-index: 0;
    width: calc(100% - var(--sidebar-width));
    padding-bottom: 28px;
    box-sizing: border-box;
  }

.graph-wrapper {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
}

.side-container {
  position: relative;
  /* min-width: 10vw; */
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  max-width: var(--sidebar-width);
  display: flex;
  flex-direction: row;
  justify-content: stretch;
  flex-shrink: 0;
  z-index: 1;
}

.network-graph {
  flex: 1 1 auto;
  min-height: 0;
  background: #252526;
  overflow: hidden;
  position: absolute;
  inset: 0;
}

.selection-rect {
  position: absolute;
  border: 1px solid rgba(0, 122, 204, 0.9);
  pointer-events: none;
  z-index: 5;
}

.webshell {
  flex: 0 0 auto;
  height: auto;
  background: black;
  color: white;
  border-top: 2px solid #444;
  overflow: hidden;
  position: relative;
  z-index: 1;
  margin-top: 0;
}

.webshell :deep(.webshell-container.minimized) {
  transform: translateY(-24px);
}

.node-context-menu {
  position: fixed;
  z-index: 10;
  background: #1f1f1f;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

.node-context-item {
  background: transparent;
  border: none;
  color: #e5e5e5;
  padding: 6px 8px;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.85rem;
}

.node-context-item:hover {
  background: #2f2f2f;
}

.confirm-reset {
  text-align: left;
  color: #1e293b;
}

.confirm-reset__text {
  margin: 0 0 16px;
  font-size: 0.95rem;
}

.iperf-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.iperf-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.iperf-label {
  font-size: 0.85rem;
  color: #1f2937;
}

.iperf-select {
  border: 1px solid #cbd5f5;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 0.85rem;
  background: #f8fafc;
}

.iperf-select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.iperf-select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.iperf-run {
  align-self: flex-start;
  background: #007acc;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.85rem;
  cursor: pointer;
}

.iperf-run:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.iperf-error {
  color: #b91c1c;
  font-size: 0.85rem;
}

.iperf-result pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  white-space: pre-wrap;
}

.confirm-reset__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.help-modal {
  color: #1e293b;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 460px;
  height: 320px;
  min-width: 420px;
  min-height: 280px;
  padding: 20px;
  box-sizing: border-box;
}

.help-modal__logo {
  width: 210px;
  height: auto;
  align-self: center;
  margin-bottom: 8px;
}

.help-modal h4 {
  margin: 4px 0 0;
  font-size: 0.95rem;
}

.help-modal p {
  margin: 0;
  font-size: 0.9rem;
}

.help-link {
  color: #2563eb;
  text-decoration: underline;
}

.confirm-reset__button {
  border: 1px solid #cbd5f5;
  border-radius: 6px;
  padding: 6px 12px;
  background: #f8fafc;
  color: #0f172a;
  cursor: pointer;
  font-size: 0.85rem;
}

.confirm-reset__button--cancel:hover {
  background: #e2e8f0;
}

.confirm-reset__button--danger {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

.confirm-reset__button--danger:hover {
  background: #dc2626;
}

.settings-modal {
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: left;
  color: #1e293b;
}

.settings-group {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.settings-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.95rem;
}

.settings-toggle input {
  width: 16px;
  height: 16px;
}

.settings-input {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
}

.settings-input input {
  border: 1px solid #cbd5f5;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 0.85rem;
}

.settings-link {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 6px;
}

.settings-link-title {
  font-size: 0.9rem;
  font-weight: 600;
}

.settings-link-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.settings-link-grid label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8rem;
}

.settings-link-grid input {
  border: 1px solid #cbd5f5;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 0.8rem;
}

.settings-inline {
  align-items: center;
  flex-direction: row;
}
</style>
