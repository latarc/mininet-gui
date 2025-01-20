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
} from "../core/api";
import { options } from "../core/options";
import Side from "./Side.vue";
import Modal from "./Modal.vue";
import ControllerForm from "./ControllerForm.vue";
import TopologyForm from "./TopologyForm.vue";

import switchImg from "@/assets/switch.svg";
import hostImg from "@/assets/host.svg";
import controllerImg from "@/assets/controller.svg";
</script>

<template>
  <Side
    @toggleAddEdgeMode="handleToggleAddEdgeMode"
    @deleteSelected="doDeleteSelected"
    @runPingall="showPingallModal"
    @closeAllActiveModes="closeAllActiveModes"
    @toggleShowHosts="toggleShowHosts"
    @toggleShowControllers="toggleShowControllers"
    @createTopology="showTopologyFormModal"
    @resetTopology="resetTopology"
    @exportTopology="exportTopology"
    @importTopology="importTopology"
    @doSelectAll="doSelectAll"
    @exportMininetScript="exportMininetScript"
    @keydown.ctrl.a.prevent="doSelectAll"
    :networkStarted="networkStarted"
    :addEdgeMode="addEdgeMode"
  />
  <div
    ref="graph"
    id="network-graph"
    class="network-graph"
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
<Teleport to="body">
<modal :show="showModal" @close="showModal = false;">
  <template #header>
    <h3>{{modalHeader}}</h3>
  </template>
  <template #body>
    <span v-html="modalContents"></span>
    <controller-form v-if="controllerModalIsActive" @form-submit="handleControllerFormSubmit" />
    <topology-form v-if="topologyModalIsActive" :controllers="controllers" @form-submit="handleTopologyFormSubmit" />
  </template>
</modal>
</Teleport>
</template>

<script>
export default {
  name: "NetworkGraph",
  components: {
    Side,
    ControllerForm,
    TopologyForm,
  },
  data() {
    return {
      hosts: new Object(),
      switches: new Object(),
      controllers: new Object(),
      links: new Array(),
      nodes: new DataSet(),
      edges: new DataSet(),
      addEdgeMode: false,
      networkStarted: true,
      showModal: false,
      controllerModalIsActive: false,
      topologyModalIsActive: false,
      formData: null,
      modalPromiseResolve: null,
      modalContents: "",
      modalHeader: "",
      controllersHidden: true,
      hostsVisible: true,
    };
  },
  computed: {
    network() {
      console.log("computed ran again");
      return this.computeNetwork();
    }
  },
  async mounted() {
    this.setupNetwork();
  },
  methods: {
    computeNetwork() {
      if (this.network) {
        return this.network;
      }
      return new Network(this.$refs.graph, {nodes: this.nodes, edges: this.edges}, options);
    },
    async setupNetwork() {
      this.networkStarted = await isNetworkStarted()
      this.hosts = await getHosts();
      this.switches = await getSwitches();
      this.controllers = await getControllers();
      Object.values(this.hosts).map((host) => {
        host.shape = "circularImage",
        host.color = {
          background: "#ffffffff",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        };
        host.image = hostImg;
        return host;
      });
      Object.values(this.switches).map((sw) => {
        sw.shape = "circularImage",
        sw.color = {
          background: "#ffffffff",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        };
        sw.image = switchImg;
        return sw;
      });
      Object.values(this.controllers).map((ctl) => {
        ctl.shape = "circularImage",
        ctl.color = {
          background: "#ffffffff",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        };
        ctl.image = controllerImg;
        return ctl;
      });
      this.links = await getEdges();
      for (const link of this.links) {
        this.edges.add({
          from: link[0],
          to: link[1],
          color: this.networkStarted? "#00ff00ff" : "#999999ff",
        });
      }
      for (const sw in this.switches) {
        let ctl = this.switches[sw].controller;
        if (ctl)
          this.edges.add({from: sw, to: ctl, color: "#ff00006f", dashes: [10, 10]})
      }
      const nodes = new DataSet([
        ...Object.values(this.hosts),
        ...Object.values(this.switches),
        ...Object.values(this.controllers),
      ]);
      this.nodes = nodes;
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
            let from = this.nodes.get(data.from)
            let to = this.nodes.get(data.to);
            if (from.type === "controller" && to.type === "controller") {
                alert("cannot connect controller with controller");
                return;
            } else if (from.type === "controller" || to.type === "controller") {
                if (from.type === "host" || to.type === "host") {
                    alert("cannot associate host with controller");
                    return;
                }
                let [sw, ctl] = (from.type === "controller") ? [to, from] : [from, to];
                sw.controller = ctl.id;
                await assocSwitch(sw.id, ctl.id);
                data.color = {color: "#ff00006f"};
                data.dashes = [10, 10];
            } else {
              let link = await deployLink(data.from, data.to);
              data.id = link.id;
              data.color = {color: this.networkStarted? "#00ff00ff" : "#999999ff"};
            }
            callback(data);
            this.enterAddEdgeMode();
          },
          deleteNode: async (data, callback) => {
            console.log("node deletion", data);
            // the deletion must happen synchronously, because mininet
            // cannot handle creating/deleting two things at the same time
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
              // the deletion must happen synchronously, because mininet
              // cannot handle creating/deleting two things at the same time
              for (const edge of data.edges) {
                  let link = this.edges.get(edge)
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
              data.edges = results
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
        this.handleNodeDragEnd(event)
      });
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
          background: "#ffffffff",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        },
      };
      host.label = `${host.name}`;
      host.image = hostImg;
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
      return host
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
          background: "#ffffffff",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        },
      };
      sw.label = `${sw.name} <${this.intToDpid(swId)}>`;
      sw.image = switchImg;
      if (switchData) {
        sw.x = switchData.x;
        sw.y = switchData.y;
      }
      sw.image = switchImg;
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
      } else {
        throw "Could not create sw " + swId;
      }
      if (switchData.controller && await assocSwitch(sw.id, switchData.controller)) {
        this.switches[sw.name].controller = switchData.controller
        this.edges.add({to: sw.id, from: switchData.controller, color: {color: "#ff00006f"}, dashes: [10, 10]})
      }
      return sw
    },
    async showControllerFormModal(position){
      this.modalHeader = "Controller Form";
      this.showModal = true;
      this.modalContents = ""
      this.controllerModalIsActive = true;
      this.topologyModalIsActive = false;
      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });
      console.log("GOT DATA")
      console.log(this.formData)
      await this.createController(position, this.formData.type === "remote", this.formData.ip, this.formData.port)
    },
    handleControllerFormSubmit(data) {
      this.formData = data;

      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }

      this.controllerModalIsActive = false;
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
          background: "#ffffffff",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        },
      };
      if (remote) ctl.label = `${ctl.name} <${ctl.ip}:${ctl.port}>`;
      else ctl.label = `${ctl.name}`;
      ctl.image = controllerImg;
      // TODO fix in backend, this takes too long because of mininet telnet check ip:port
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
      if (data === "draggable-host") {
        this.createHost(
          this.network.DOMtoCanvas({ x: event.clientX, y: event.clientY }),
        );
      } else if (data === "draggable-switch") {
        this.createSwitch(
          this.network.DOMtoCanvas({ x: event.clientX, y: event.clientY }),
        );
      } else if (data === "draggable-controller") {
        this.showControllerFormModal(
          this.network.DOMtoCanvas({ x: event.clientX, y: event.clientY }),
        );
      }
    },
    async handleNodeDragEnd(event) {
      event.nodes.forEach(async nodeId => {
        let node = this.network.body.nodes[nodeId]
        await updateNodePosition(nodeId, [node.x, node.y])
      })
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
      this.modalContents = "";
      this.showModal = false;
    },
    closeAllActiveModes() {
      this.closeAddEdgeMode();
      this.closeModal();
    },
    handleToggleAddEdgeMode() {
      console.log("addedgemode toggle")
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
      console.log("CTRL A PRESSED")
      this.closeAllActiveModes();
      this.network.setSelection({nodes: this.nodes.getIds()});
    },
    createPingallTable(inputString) {
      const data = inputString.replaceAll("min/avg/max/mdev", "").replaceAll("/", " ").replaceAll("->", " ").replaceAll(",", "").replaceAll(":", "").replaceAll("rtt", "").split(/\s+/).filter(Boolean);
      let tableHTML = '<table border="1"><thead><tr>';
      const headers = ['src', 'dst', 'packets_sent', 'packets_recv', 'min', 'avg', 'max', 'mdev'];
      headers.forEach(header => {
          tableHTML += `<th>${header}</th>`;
      });
      tableHTML += '</tr></thead><tbody>';
      for (let i = 0; i < data.length; i += 9) {
          tableHTML += '<tr>';
          for (let j = 0; j < 8; j++) {
              tableHTML += `<td>${data[i + j]}</td>`;
          }
          tableHTML += '</tr>';
      }
      tableHTML += '</tbody></table>';
      return tableHTML;
    },
    async showPingallModal() {
      this.closeAllActiveModes();
      this.modalHeader = "Pingall Results";
      this.modalContents = "Loading...";
      this.showModal = true;
      let pingallResults = await requestRunPingall()
      if (pingallResults) {
        console.log(pingallResults)
        let pingallTable = this.createPingallTable(pingallResults)
        console.log(pingallTable)
        this.modalContents = pingallTable;
      } else {
        this.showModal = false;
      }
    },
    createSwStatsTable(jsonData) {
      let t='<table border="1">',d=jsonData;
      t+='<tr>';for(let k in d)t+='<th>'+k+'</th>';t+='</tr>';
      t+='<tr>';for(let k in d)t+='<td>'+(Array.isArray(d[k])?d[k].join('<br>'):d[k])+'</td>';t+='</tr>';
      return t+'</table>';
    },
    async showStatsModal(nodeId) {
      this.closeAllActiveModes();
      this.modalHeader = "Node Info";
      this.modalContents = `<h3>Node ${nodeId}</h3>Loading...`;
      this.showModal = true;
      let nodeStats = await getNodeStats(nodeId)
      if (nodeStats) {
        console.log(nodeStats)
        this.modalContents = this.createSwStatsTable(nodeStats);
      } else {
        this.showModal = false;
      }
    },
    async createSingleTopo(nDevices, controller) {
      let newSw = await this.createSwitch({x: 250, y: 150, controller: controller});
      for (var i=0; i<nDevices; i++) {
        let newHost = await this.createHost({x: 200+i*90, y: 300});
        let link = await deployLink(newSw.id, newHost.id);
        this.edges.add({
          from: newSw.id,
          to: newHost.id,
          color: this.networkStarted? "#00ff00ff" : "#999999ff",
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
            color: this.networkStarted ? "#00ff00ff" : "#999999ff",
          });
        }

        if (prevSw) {
          await deployLink(newSw.id, prevSw.id);
          this.edges.add({
            from: newSw.id,
            to: prevSw.id,
            color: this.networkStarted ? "#00ff00ff" : "#999999ff",
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
                color: this.networkStarted ? "#00ff00ff" : "#999999ff",
              });
            }
          }
          layer.push(node);
        }
        nodes[d] = layer;
      }
    },
    async showTopologyFormModal(){
      this.modalHeader = "Create Topology";
      this.showModal = true;
      this.modalContents = "";
      this.topologyModalIsActive = true;
      this.controllerModalIsActive = false;
      console.log("networkgraph THIS.CONTROLLERS", this.controllers)
      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });
      console.log("GOT DATA")
      console.log(this.formData)
      await this.handleCreateTopology(this.formData.type, this.formData.nDevices, this.formData.nLayers, this.formData.controller)
    },
    handleTopologyFormSubmit(data) {
      this.formData = data;
      console.log("FORM DATA", this.formData)
      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }

      this.topologyModalIsActive = false;
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
      const confirmed = window.confirm("Are you sure you want to reset the topology? This action cannot be undone.");

      if (confirmed && await requestResetNetwork()) {
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
    async exportTopology() {
      await requestExportNetwork();
    },
    async exportMininetScript() {
      await requestExportMininetScript();
    },
    async importTopology(file) {
      await this.resetTopology()
      const data = await requestImportNetwork(file);
      await this.setupNetwork();
      this.network.setData({nodes: this.nodes, edges: this.edges})
      this.network.redraw()
    }
  }
};
</script>

<style>
.network-graph {
  background-color: white;
  height: 100%;
  width: 100%;
  position: absolute;
  z-index: 0;
}
</style>
