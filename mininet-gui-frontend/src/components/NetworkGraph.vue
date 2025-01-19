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
  requestImportNetwork,
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
    <topology-form v-if="topologyModalIsActive" @form-submit="handleTopologyFormSubmit" />
    
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
      controllers: new Array(),
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
                data.dashes = [5, 5];
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
            console.log("edge deletion", data);
            console.log("this is the network:", this.network);
            console.log("this is the edges dataset:", this.edges.get());
            try {
              const results = [];
              // the deletion must happen synchronously, because mininet
              // cannot handle creating/deleting two things at the same time
              for (const edge of data.edges) {
                  console.log(edge, "deletion");
                  const result = await deleteLink(edge);
                  results.push(edge);
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
    async createSwitch(position) {
      let swId = Object.values(this.switches).length + 1;
      while (`s${swId}` in this.switches) {
        swId++;
      }
      let sw = {
        id: `s${swId}`,
        type: "sw",
        name: `s${swId}`,
        label: null,
        ports: 4,
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
      if (position) {
        sw.x = position.x;
        sw.y = position.y;
      }
      sw.image = switchImg;
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
      } else {
        throw "Could not create sw " + swId;
      }
      return sw
    },
    async showControllerFormModal(position){
      this.modalHeader = "Controller Form";
      this.showModal = true;
      this.controllerModalIsActive = true;
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
        let node = this.nodes.get(nodeId)
        // TODO: fix this calculation, does not work well with canvas zoom in/out
        node.x += event.event.deltaX
        node.y += event.event.deltaY
        
        this.nodes.updateOnly(node)
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
    // async startNetwork() {
    //   this.closeAllActiveModes();
    //   console.log("edges:",this.edges);
    //   if (await requestStartNetwork()) {
    //     this.networkStarted = true;
    //     this.edges.forEach((item, id) => {
    //         if (item.color == "#999999ff") {
    //             item.color = {color: "#00ff00ff"};
    //             this.edges.updateOnly(item);
    //         }
    //     });
    //   }
    // },
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
    async createSingleTopo(nDevices) {
      let newSw = await this.createSwitch({x: 250,y: 150});
      for (var i=0; i<nDevices; i++) {
        let newHost = await this.createHost({x: 200+i*90, y: 300});
        console.log("newSw")
        console.log("newSw", newSw)
        console.log("newHost")
        console.log("newHost", newHost)
        let link = await deployLink(newSw.id, newHost.id);
        this.edges.add({
          from: newSw.id,
          to: newHost.id,
          color: this.networkStarted? "#00ff00ff" : "#999999ff",
        });
      }
    },
    async createLinearTopo(nDevices) {
      let prevSw = null;
      for (var i=0; i<nDevices; i++) {
        let newSw = await this.createSwitch({x: 250+i*90,y: 150});
        let newHost = await this.createHost({x: 200+i*90, y: 300});
        console.log("newSw")
        console.log("newSw", newSw)
        console.log("newHost")
        console.log("newHost", newHost)
        if (prevSw != null) {
          await deployLink(newSw.id, prevSw.id);
          this.edges.add({
            from: newSw.id,
            to: prevSw.id,
            color: this.networkStarted? "#00ff00ff" : "#999999ff",
          });
        }
        await deployLink(newSw.id, newHost.id);
        this.edges.add({
          from: newSw.id,
          to: newHost.id,
          color: this.networkStarted? "#00ff00ff" : "#999999ff",
        });
        prevSw = newSw;
      }
    },
    async createTreeTopo(depth, fanout) {
      const addTree = async (currentDepth, offset) => {
        const isSwitch = currentDepth < depth;
        let node;

        if (isSwitch) {
          node = await this.createSwitch({x: 100 + offset,y: 150 + currentDepth*90});
          console.log("Created Switch:", node);

          for (let i = 0; i < fanout; i++) {
            const child = await addTree(currentDepth + 1, i*100+fanout*currentDepth*offset);
            await deployLink(node.id, child.id);
            this.edges.add({
              from: node.id,
              to: child.id,
              color: this.networkStarted ? "#00ff00ff" : "#999999ff",
            });
          }
        } else {
          node = await this.createHost({ x: 100 + offset, y: 150 + currentDepth*90 });
          console.log("Created Host:", node);
        }

        return node;
      };

      await addTree(0, fanout);
    },
    async showTopologyFormModal(){
      this.modalHeader = "Create Topology";
      this.showModal = true;
      this.topologyModalIsActive = true;
      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });
      console.log("GOT DATA")
      console.log(this.formData)
      await this.handleCreateTopology(this.formData.type, this.formData.nDevices, this.formData.nLayers)
    },
    handleTopologyFormSubmit(data) {
      this.formData = data;

      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }

      this.topologyModalIsActive = false;
      this.showModal = false;
    },
    async handleCreateTopology(topologyType, nDevices, nLayers){
      console.log("Received createTopology event with:", topologyType, "data", nDevices);
      if (topologyType == "Single") {
        await this.createSingleTopo(nDevices);
      } else if (topologyType == "Linear") {
        await this.createLinearTopo(nDevices);
      } else if (topologyType == "Tree") {
        await this.createTreeTopo(nLayers, nDevices);
      }
    },
    async resetTopology() {
      // confirm? (this will delete the current topology)
      if (await requestResetNetwork()) {
        console.log("resetting topology")
        this.hosts = new Object()
        this.switches = new Object()
        this.controllers = new Array()
        this.links = new Array()
        this.nodes = new DataSet()
        this.edges = new DataSet()
        this.network.setData({nodes: this.nodes, edges:  this.edges})
        this.network.redraw()
      }
    },
    async exportTopology() {
      console.log("Exporting JSON")
      await requestExportNetwork();
    },
    async importTopology(file) {
      console.log(file)
      await this.resetTopology()
      const data = await requestImportNetwork(file);
      await this.setupNetwork();
      this.network.setData({nodes: this.nodes, edges:  this.edges})
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
/* 
.vis-network-graph {
  height: 100%;
  width: inherit;
  position: absolute
} */
</style>
