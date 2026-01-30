<script setup>
import { Network } from "vis-network/peer";
import { DataSet } from "vis-data/peer";

import {
  getHosts,
  getSwitches,
  getControllers,
  getEdges,
  getNodeStats,
  deployHost,
  deployLink,
  deployController,
  deploySwitch,
  assocSwitch,
  isNetworkStarted,
  requestResetNetwork,
  requestRunPingall,
  deleteNode,
  deleteLink,
  updateNodePosition,
  requestExportNetwork,
  requestExportMininetScript,
  requestImportNetwork,
  removeAssociation,
  getSnifferState,
  startSniffer,
  stopSniffer,
  exportSnifferPcap,
} from "../core/api";
import { options } from "../core/options";
import Side from "./Side.vue";
import Modal from "./Modal.vue";
import Webshell from "./Webshell.vue";
import NodeStats from "./NodeStats.vue";
import PingallResults from "./PingallResults.vue";
import ControllerForm from "./ControllerForm.vue";
import TopologyForm from "./TopologyForm.vue";

import switchImg from "@/assets/light-switch.svg";
import hostImg from "@/assets/light-host.svg";
import controllerImg from "@/assets/light-controller.svg";
</script>

<template>
  <div class="layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- Side panel (left) -->

      <div class="side-container">
        <Side
          @toggleAddEdgeMode="handleToggleAddEdgeMode"
          @deleteSelected="doDeleteSelected"
          @runPingall="showPingallModal"
          @closeAllActiveModes="closeAllActiveModes"
          @toggleShowHosts="toggleShowHosts"
          @toggleShowControllers="toggleShowControllers"
          @createTopology="showTopologyFormModal"
          @resetTopology="showResetConfirmModal"
          @toggleSniffer="toggleSniffer"
          @exportSniffer="exportSniffer"
          @toggleSidebar="handleSidebarToggle"
          @exportTopology="exportTopology"
          @importTopology="importTopology"
          @doSelectAll="doSelectAll"
          @exportMininetScript="exportMininetScript"
          @openSettings="showSettingsModal"
          @keydown.ctrl.a.prevent="doSelectAll"
          :networkStarted="networkStarted"
          :addEdgeMode="addEdgeMode"
          :snifferActive="snifferActive"
          :pingallRunning="pingallRunning"
        />
      </div>
    
    <!-- Main Content (Graph + WebShell) -->
    <div class="main-content">
      <div ref="graph" id="network-graph" class="network-graph"
        @drop.prevent="handleDrop"
        @dragenter.prevent
        @dragover.prevent
        @keydown.esc="closeAllActiveModes"
        @keydown.h="toggleShowHosts"
        @keydown.c="toggleShowControllers"
        @keydown.e="enterAddEdgeMode"
        @keydown.d="doDeleteSelected"
        @keydown.delete="doDeleteSelected"
        @keydown.ctrl.a.prevent="doSelectAll"
      ></div>

      <!-- WebShell at the bottom -->
      <webshell
        class="webshell"
        :nodes="nodes"
        :edges="edges"
        :snifferActive="snifferActive"
        :preferredView="webshellView"
        :focusNodeId="webshellFocusId"
        :openaiKey="settings.openaiApiKey"
        :llmHandlers="llmHandlers"
        @viewChange="handleWebshellViewChange"
      />
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
        <node-stats v-if="modalOption === 'nodeStats'" :stats="modalData" />
        <pingall-results v-if="modalOption === 'pingall'" :pingResults="modalData" />
        <controller-form v-if="modalOption === 'controllerForm'" @form-submit="handleControllerFormSubmit" />
        <topology-form v-if="modalOption === 'topologyForm'" :controllers="controllers" @form-submit="handleTopologyFormSubmit" />
        <div v-if="modalOption === 'settings'" class="settings-modal">
          <div class="settings-group">
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
    PingallResults,
    ControllerForm,
    TopologyForm,
  },
  data() {
    return {
      hosts: {},
      switches: {},
      controllers: {},
      links: [],
      nodes: new DataSet(),
      edges: new DataSet(),
      addEdgeMode: false,
      networkStarted: true,
      pingallRunning: false,
      snifferActive: false,
      sidebarCollapsed: false,
      showModal: false,
      modalHeader: "",
      modalOption: null,
      modalData: {},
      webshellView: null,
      webshellFocusId: null,
      webshellActiveView: null,
      settings: {
        showHostIp: false,
        showSwitchDpids: false,
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
    }
  },
  async mounted() {
    this.loadSettings();
    await this.syncSnifferState();
    this.snifferStateTimer = setInterval(this.syncSnifferState, 5000);
    this.setupNetwork();
  },
  beforeUnmount() {
    if (this.snifferStateTimer) clearInterval(this.snifferStateTimer);
  },
  methods: {
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
    },
    persistSettings() {
      try {
        localStorage.setItem("mininetGuiSettings", JSON.stringify(this.settings));
      } catch (error) {
        console.warn("Failed to persist settings", error);
      }
      this.applyHostLabels();
      this.applySwitchLabels();
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
      this.networkStarted = await isNetworkStarted();
      this.hosts = await getHosts();
      this.switches = await getSwitches();
      this.controllers = await getControllers();

      Object.values(this.hosts).map((host) => {
        host.shape = "circularImage";

        host.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#007acc", border: "#007acc" },
        };
        host.image = hostImg;
        host.label = this.hostLabel(host);
        return host;
      });

      Object.values(this.switches).map((sw) => {
        sw.shape = "circularImage";
        sw.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#007acc", border: "#007acc" },
        };
        sw.image = switchImg;
        sw.label = this.switchLabel(sw);
        return sw;
      });

      Object.values(this.controllers).map((ctl) => {
        ctl.shape = "circularImage";
        ctl.color = {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#007acc", border: "#007acc" },
        };
        ctl.image = controllerImg;
        return ctl;
      });

      this.links = await getEdges();
      for (const link of this.links) {
        const options = link.options || null;
        this.edges.add({
          from: link.from,
          to: link.to,
          color: this.networkStarted ? "#00aa00ff" : "#999999ff",
          title: this.formatLinkTitle(options),
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
      ]);
      this.nodes = nodes;
      this.selectInitialWebshell();
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
            }
            callback(data);
            this.enterAddEdgeMode();
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
        }
      });
      this.network.on("dragEnd", async (event) => {
        this.handleNodeDragEnd(event);
      });
    },
    selectInitialWebshell() {
      const allNodes = [
        ...Object.values(this.hosts || {}),
        ...Object.values(this.switches || {}),
        ...Object.values(this.controllers || {}),
      ];
      if (allNodes.length === 0) {
        this.webshellView = "logs";
        this.webshellFocusId = null;
        return;
      }
      const lowest = this.getLowestNodeId(allNodes.map((node) => node.id));
      this.webshellView = "terminal";
      this.webshellFocusId = null;
      this.$nextTick(() => {
        this.webshellFocusId = lowest;
      });
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
    focusWebshell(nodeId) {
      if (this.webshellActiveView === "chat") return;
      this.webshellView = "terminal";
      this.webshellFocusId = null;
      this.$nextTick(() => {
        this.webshellFocusId = nodeId;
      });
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
      this.edges.add({
        from: fromId,
        to: toId,
        color: { color: this.networkStarted ? "#00aa00ff" : "#999999ff" },
        title: this.formatLinkTitle(options),
      });
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
        await this.createController({ x: entry.x, y: entry.y }, remote, ip, port);
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
          highlight: { background: "#007acc", border: "#007acc" },
        },
      };
      host.label = this.hostLabel(host);
      host.image = hostImg;
      if (position) {
        host.x = position.x;
        host.y = position.y;
      }
      if (await deployHost(host)) {
        this.nodes.add(host);
        this.hosts[host.name] = host;
        this.focusWebshell(host.id);
      } else {
        throw "Could not create host " + hostId;
      }
      return host;
    },
    async createSwitch(switchData) {
      let swId = Object.values(this.switches).length + 1;
      while (`s${swId}` in this.switches) {
        swId++;
      }
      let sw = {
        id: `s${swId}`,
        type: "sw",
        name: `s${swId}`,
        label: switchData.label || null,
        ports: switchData.ports || 4,
        controller: null,
        shape: "circularImage",
        color: {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#007acc", border: "#007acc" },
        },
      };
      sw.label = this.switchLabel(sw);
      sw.image = switchImg;
      if (switchData) {
        sw.x = switchData.x;
        sw.y = switchData.y;
      }
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
        this.focusWebshell(sw.id);
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
    async showControllerFormModal(position) {
      this.modalHeader = "Controller Form";
      this.modalOption = "controllerForm";
      this.showModal = true;

      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });

      console.log("GOT DATA:", this.formData);
      await this.createController(position, this.formData.type === "remote", this.formData.ip, this.formData.port);
    },
    handleControllerFormSubmit(data) {
      this.formData = data;
      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }
      this.showModal = false;
    },
    async createController(position, remote, ip, port) {
      let ctlId = Object.values(this.controllers).length + 1;
      while (`c${ctlId}` in this.controllers) {
        ctlId++;
      }
      let ctl = {
        id: `c${ctlId}`,
        type: "controller",
        name: `c${ctlId}`,
        label: null,
        remote: remote,
        ip: ip,
        port: port,
        x: position.x,
        y: position.y,
        shape: "circularImage",
        color: {
          background: "#252526",
          border: "#00000000",
          highlight: { background: "#007acc", border: "#007acc" },
        },
      };
      if (remote) ctl.label = `${ctl.name} <${ctl.ip}:${ctl.port}>`;
      else ctl.label = `${ctl.name}`;
      ctl.image = controllerImg;
      if (await deployController(ctl)) {
        this.nodes.add(ctl);
        this.controllers[ctl.name] = ctl;
        this.focusWebshell(ctl.id);
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
      } else if (data === "draggable-switch") {
        this.createSwitch(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-controller") {
        this.showControllerFormModal(
          this.network.DOMtoCanvas(domPoint),
        );
      }
    },
    async handleNodeDragEnd(event) {
      event.nodes.forEach(async nodeId => {
        let node = this.network.body.nodes[nodeId];
        await updateNodePosition(nodeId, [node.x, node.y]);
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
    },
    closeAllActiveModes() {
      this.closeAddEdgeMode();
      this.closeModal();
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
      this.hostsHidden = !this.hostsHidden;
      this.nodes.forEach((node, id) => {
        if (node.type == "host") {
          node.hidden = this.hostsHidden;
          this.nodes.updateOnly(node);
        }
      });
    },
    toggleShowControllers () {
      this.controllersHidden = !this.controllersHidden;
      this.nodes.forEach((node, id) => {
        if (node.type == "controller") {
          node.hidden = this.controllersHidden;
          this.nodes.updateOnly(node);
        }
      });
    },
    async doDeleteSelected() {
      this.closeAllActiveModes();
      this.network.deleteSelected();
    },
    doSelectAll() {
      console.log("CTRL A PRESSED");
      this.closeAllActiveModes();
      this.network.setSelection({nodes: this.nodes.getIds()});
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
    async showStatsModal(nodeId) {
      this.closeAllActiveModes();
      this.modalHeader = `Node Info: ${nodeId}`;
      this.modalOption = "nodeStats";
      let nodeStats = await getNodeStats(nodeId);
      console.log("nodeStats", nodeStats);
      this.modalData = nodeStats || null;
      this.showModal = true;
    },
    async createSingleTopo(nDevices, controller) {
      let newSw = await this.createSwitch({x: 250, y: 150, controller: controller});
      for (var i=0; i<nDevices; i++) {
        let newHost = await this.createHost({x: 200+i*90, y: 300});
        let link = await deployLink(newSw.id, newHost.id);
        this.edges.add({
          from: newSw.id,
          to: newHost.id,
          color: this.networkStarted ? "#00aa00ff" : "#999999ff",
        });
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

          await deployLink(newSw.id, newHost.id);
          this.edges.add({
            from: newSw.id,
            to: newHost.id,
            color: this.networkStarted ? "#00aa00ff" : "#999999ff",
          });
        }

        if (prevSw) {
          await deployLink(newSw.id, prevSw.id);
          this.edges.add({
            from: newSw.id,
            to: prevSw.id,
            color: this.networkStarted ? "#00aa00ff" : "#999999ff",
          });
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
              await deployLink(node.id, child.id);
              this.edges.add({
                from: node.id,
                to: child.id,
                color: this.networkStarted ? "#00aa00ff" : "#999999ff",
              });
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
      if (await requestResetNetwork()) {
        this.snifferActive = false;
        console.log("Resetting topology");
        this.hosts = new Object();
        this.switches = new Object();
        this.controllers = new Object();
        this.links = new Array();
        this.nodes = new DataSet();
        this.edges = new DataSet();
        this.network.setData({ nodes: this.nodes, edges: this.edges });
        this.network.redraw();
      }
    },
    handleSidebarToggle(isActive) {
      this.sidebarCollapsed = !isActive;
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
    async exportMininetScript() {
      await requestExportMininetScript();
    },
    async importTopology(file) {
      await this.resetTopology();
      const data = await requestImportNetwork(file);
      await this.setupNetwork();
      this.network.setData({nodes: this.nodes, edges: this.edges});
      this.network.redraw();
    }
  }
};
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
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
  height: 100vh;
  min-height: 0;
  min-width: 0;
  position: relative;
  z-index: 0;
  width: calc(100% - var(--sidebar-width));
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
}

.webshell {
  flex: 0 0 auto;
  height: auto;
  background: black;
  color: white;
  border-top: 2px solid #444;
  overflow: auto;
  position: relative;
  z-index: 1;
}

.confirm-reset {
  text-align: left;
  color: #1e293b;
}

.confirm-reset__text {
  margin: 0 0 16px;
  font-size: 0.95rem;
}

.confirm-reset__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
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
