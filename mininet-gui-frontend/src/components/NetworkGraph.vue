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
} from "../core/api";
import { options } from "../core/options";
import Side from "./Side.vue";

import switchImg from "@/assets/switch.svg";
import hostImg from "@/assets/host.svg";
</script>

<template>
  <Side @addEdgeMode="enterAddEdgeMode" @networkStart="startNetwork" :networkStarted="networkStarted" @runPingall="showPingallModal"/>
  <div
    ref="graph"
    id="network-graph"
    class="network-graph"
    @drop.prevent="handleDrop"
    @dragenter.prevent
    @dragover.prevent
></div>
</template>

<script>
export default {
  name: "NetworkGraph",
  components: {
    Side,
  },
  data() {
    return {
      network: Network,
      hosts: Object,
      switches: Object,
      links: Array,
      nodes: DataSet,
      edges: DataSet,
      addEdgeMode: Function,
      networkStarted: false,
    };
  },
  async mounted() {
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
    const net = new Network(this.$refs.graph, { nodes, edges }, options);
    this.network = net;
    this.addEdgeMode = this.network.addEdgeMode.bind(net); // why use state when you can bind?
    this.networkStarted = await isNetworkStarted()
  },
  methods: {
    async createHost(position) {
      let host_id = Object.values(this.hosts).length + 1;
      while (`h${host_id}` in this.hosts) {
        host_id++;
      }
      let host = {
        id: `h${host_id}`,
        type: "host",
        name: `h${host_id}`,
        label: null,
        ip: `10.0.0.${host_id}/8`,
        mac: host_id.toString(16).toUpperCase().padStart(12, "0"),
        x: position.x,
        y: position.y,
      };
      host.label = host.name;
      host.image = hostImg;
      host.shape = "image";
      if (await deployHost(host)) {
        this.nodes.add(host);
        this.hosts[host.name] = host;
        this.next_host_id = host_id + 1;
      } else {
        throw "Could not create host " + host_id;
      }
    },
    async createSwitch(position) {
      let sw_id = Object.values(this.switches).length + 1;
      while (`s${sw_id}` in this.switches) {
        sw_id++;
      }
      let sw = {
        id: `s${sw_id}`,
        type: "sw",
        name: `s${sw_id}`,
        label: null,
        ports: 4,
        controller: "c0",
        x: position.x,
        y: position.y,
      };
      sw.label = sw.name;
      sw.image = switchImg;
      sw.shape = "image";
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
        this.next_sw_id = sw_id + 1;
      } else {
        throw "Could not create sw " + sw_id;
      }
    },
    handleDrop(event) {
      event.preventDefault();
      var data = event.dataTransfer.getData("text").split("/").slice(-1)[0];
      if (data === "host.svg") {
        this.createHost(
          this.network.DOMtoCanvas({ x: event.clientX, y: event.clientY }),
        );
      } else if (data === "switch.svg") {
        this.createSwitch(
          this.network.DOMtoCanvas({ x: event.clientX, y: event.clientY }),
        );
      }
    },
    enterAddEdgeMode() {
      this.addEdgeMode();
    },
    async startNetwork() {
      await requestStartNetwork();
      this.networkStarted = true;
    },
    async showPingallModal() {
      let pingallResults = await requestRunPingall()
      console.log(pingallResults)
      //this.showPingallModal = true;
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
