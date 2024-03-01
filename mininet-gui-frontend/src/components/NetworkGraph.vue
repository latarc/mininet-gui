<script setup>
import { Network } from "vis-network/peer";
import { DataSet } from "vis-data/peer";

import {
  getHosts,
  getSwitches,
  getEdges,
  deployHost,
  deploySwitch,
  isNetworkStarted,
  requestStartNetwork,
  requestRunPingall,
  deployLink,
  deleteNode,
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
      host.image = hostImg;
      host.shape = "image";
      return host;
    });
    Object.values(this.switches).map((sw) => {
      sw.image = switchImg;
      sw.shape = "image";
      return sw;
    });
    this.links = await getEdges();
    let links = [];
    for (var link in this.links) {
      links.push({
        from: this.links[link][0],
        to: this.links[link][1],
      });
    }
    const nodes = new DataSet([
      ...Object.values(this.hosts),
      ...Object.values(this.switches),
    ]);
    this.nodes = nodes;
    const edges = new DataSet(links);
    this.edges = edges;
    console.log("network inside mounted, before setup:", this.network);
    await this.setupNetwork();
  },
  methods: {
    setupNetwork() {
      this.network.setOptions({
        manipulation: {
          enabled: false,
          addEdge: async (data, callback) => {
            console.log("addEdge data, callback:", data, callback);
            if (data.from == data.to) {
              confirm("Cannot connect node to itself");
              return;
            }
            if (await deployLink(data.from, data.to)) {
              callback(data);
              this.network.addEdgeMode();
            }
          },
          deleteNode: async (data, callback) => {
            if (data["nodes"]) {
              await deleteNode(data["nodes"][0]);
              callback(data);
            }
          },
        },
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
      };
      host.label = `${host.name}`;
      host.image = hostImg;
      host.shape = "image";
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
      };
      sw.label = `${sw.name} <${this.intToDpid(swId)}>`;
      sw.image = switchImg;
      sw.shape = "image";
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
        this.nextSwId = swId + 1;
      } else {
        throw "Could not create sw " + swId;
      }
    },
    handleDrop(event) {
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
    closeAddEdgeMode() {
        this.addEdgeMode = false;
        this.network.disableEditMode;
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
      if (!this.addEdgeMode) {
        this.addEdgeMode = true;
        this.network.addEdgeMode();
      } else {
        this.closeAddEdgeMode();
      }
    },
    doDeleteSelected() {
      this.network.deleteSelected();
    },
    async startNetwork() {
      if (await requestStartNetwork())
        this.networkStarted = true;
    },
    async showPingallModal() {
      this.modalHeader = "Pingall Results";
      this.modalContents = "Loading...";
      this.showModal = true;
      let pingallResults = await requestRunPingall()
      console.log(pingallResults)
      this.modalContents = pingallResults.replace("\n", "<br>");
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
