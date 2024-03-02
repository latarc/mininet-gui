<script setup>
import { Network } from "vis-network/peer";
import { DataSet } from "vis-data/peer";

import {
  getHosts,
  getSwitches,
  getEdges,
  getNodeStats,
  deployHost,
  deploySwitch,
  isNetworkStarted,
  requestStartNetwork,
  requestRunPingall,
  deployLink,
  deleteNode,
  deleteLink,
} from "../core/api";
import { options } from "../core/options";
import Side from "./Side.vue";
import Modal from "./Modal.vue";

import switchImg from "@/assets/switch.svg";
import hostImg from "@/assets/host.svg";
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
    this.links = await getEdges();
    for (var link in this.links) {
      this.edges.add({
        from: this.links[link][0],
        to: this.links[link][1],
      });
    }
    const nodes = new DataSet([
      ...Object.values(this.hosts),
      ...Object.values(this.switches),
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
            let link = await deployLink(data.from, data.to);
            data.id = link.id;
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
        this.nextHostId = hostId + 1;
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
        controller: "c0",
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
      //sw.shape = "image";
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
        this.nextSwId = swId + 1;
      } else {
        throw "Could not create sw " + swId;
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
