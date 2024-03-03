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
  requestStartNetwork,
  requestRunPingall,
  deleteNode,
  deleteLink,
} from "../core/api";
import { options } from "../core/options";
import Side from "./Side.vue";
import Modal from "./Modal.vue";

import switchImg from "@/assets/switch.svg";
import hostImg from "@/assets/host.svg";
import controllerImg from "@/assets/controller.svg";
</script>

<template>
  <Side
    @toggleAddEdgeMode="handleToggleAddEdgeMode"
    @networkStart="startNetwork"
    @deleteSelected="doDeleteSelected"
    @runPingall="showPingallModal"
    @closeAllActiveModes="closeAllActiveModes"
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
></div>
<Teleport to="body">
<modal :show="showModal" @close="showModal = false">
  <template #header>
    <h3>{{modalHeader}}</h3>
  </template>
  <template #body>
    <span v-html="modalContents"></span>
  </template>
</modal>
</Teleport>
</template>

<script>
export default {
  name: "NetworkGraph",
  components: {
    Side,
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
      networkStarted: false,
      showModal: false,
      modalContents: "",
      modalHeader: "",
    };
  },
  computed: {
    network() {
      console.log("computed ran again");
      if (this.network) {
        this.network
        return this.network;
      }
      return new Network(this.$refs.graph, {nodes: this.nodes, edges: this.edges}, options);
    }
  },
  async mounted() {
    this.networkStarted = await isNetworkStarted()
    this.hosts = await getHosts();
    this.switches = await getSwitches();
    this.controllers = await getControllers();
    Object.values(this.hosts).map((host) => {
      host.shape = "circularImage",
      host.color = {
        background: "#ffffff00",
        border: "#ffffff00",
        highlight: { background: "red", border: "blue" },
      };
      host.image = hostImg;
      return host;
    });
    Object.values(this.switches).map((sw) => {
      sw.shape = "circularImage",
      sw.color = {
        background: "#ffffff00",
        border: "#ffffff00",
        highlight: { background: "red", border: "blue" },
      };
      sw.image = switchImg;
      return sw;
    });
    Object.values(this.controllers).map((ctl) => {
      ctl.shape = "circularImage",
      ctl.color = {
        background: "#ffffff00",
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
    await this.setupNetwork();
  },
  methods: {
    async setupNetwork() {
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
            }
            callback(data);
            this.enterAddEdgeMode();
          },
          deleteNode: async (data, callback) => {
            console.log("node deletion", data);
            Promise.all(data.nodes.map(nodeId => deleteNode(nodeId)))
              .then(results => {
                console.log("All nodes deleted:", results);
                callback(data)
              })
              .catch(error => {
                console.error("Error deleting nodes:", error);
              }); 
          },
          deleteEdge: async (data, callback) => {
            console.log("edge deletion", data);
            console.log("this is the network:", this.network);
            console.log("this is the edges dataset:", this.edges.get());
            try {
              const results = [];
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
        x: position.x,
        y: position.y,
        shape: "circularImage",
        color: {
          background: "#ffffff00",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        },
      };
      host.label = `${host.name}`;
      host.image = hostImg;
      if (await deployHost(host)) {
        this.nodes.add(host);
        this.hosts[host.name] = host;
      } else {
        throw "Could not create host " + hostId;
      }
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
        x: position.x,
        y: position.y,
        shape: "circularImage",
        color: {
          background: "#ffffff00",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        },
      };
      sw.label = `${sw.name} <${this.intToDpid(swId)}>`;
      sw.image = switchImg;
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
      } else {
        throw "Could not create sw " + swId;
      }
    },
    async createController(position) {
      let ctlId = Object.values(this.controllers).length + 1;
      while (`c${ctlId}` in this.controllers) {
        ctlId++;
      }
      let ip = "127.0.0.1";
      let port = "6653";
      let ctl = {
        id: `c${ctlId}`,
        type: "controller",
        name: `c${ctlId}`,
        label: null,
        remote: true,
        ip: ip,
        port: port,
        x: position.x,
        y: position.y,
        shape: "circularImage",
        color: {
          background: "#ffffff00",
          border: "#ffffff00",
          highlight: { background: "red", border: "blue" },
        },
      };
      ctl.label = `${ctl.name} <${ctl.ip}:${ctl.port}>`;
      ctl.image = controllerImg;
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
        this.createController(
          this.network.DOMtoCanvas({ x: event.clientX, y: event.clientY }),
        );
      }
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
    async doDeleteSelected() {
      this.closeAllActiveModes();
      this.network.deleteSelected();

    },
    async startNetwork() {
      this.closeAllActiveModes();
      if (await requestStartNetwork())
        this.networkStarted = true;
    },
    async showPingallModal() {
      this.closeAllActiveModes();
      this.modalHeader = "Pingall Results";
      this.modalContents = "Loading...";
      this.showModal = true;
      let pingallResults = await requestRunPingall()
      if (pingallResults) {
        console.log(pingallResults)
        this.modalContents = pingallResults.replace("\n", "<br>");
      } else {
        this.showModal = false;
      }
    },
    async showStatsModal(nodeId) {
      this.closeAllActiveModes();
      this.modalHeader = "Node Info";
      this.modalContents = `<h3>Node ${nodeId}</h3>Loading...`;
      this.showModal = true;
      let nodeStats = await getNodeStats(nodeId)
      if (nodeStats) {
        console.log(nodeStats)
        this.modalContents = JSON.stringify(nodeStats);
      } else {
        this.showModal = false;
      }
    }
  },
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
