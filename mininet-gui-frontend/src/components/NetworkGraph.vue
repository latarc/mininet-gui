<script setup>
  import { Network } from 'vis-network';
  import { DataSet } from 'vis-data';
  
  import { getNodes, getEdges, deployHost } from '../core/api';
  import { options } from '../core/options';
  import Side from './Side.vue'
</script>


<template>
  <Side />
  <div id="network-graph" class="network-graph" @drop.prevent="handleDrop" @dragenter.prevent @dragover.prevent></div>
</template>

<script>
export default {
  name: 'NetworkGraph',
  components: [
    "Side"
  ],
  data() {
    return {
      next_host_id: Number,
      network: Network,
      nodes: DataSet,
      edges: DataSet
    };
  },
  async mounted() {
    this.nodes = new DataSet(await getNodes());
    this.edges = new DataSet(getEdges());
    const container = document.getElementById('network-graph');
    const data = {
      nodes: this.nodes,
      edges: this.edges
    };
    this.next_host_id = this.nodes.length + 1;
    this.network = new Network(container, data, options);

  },
  methods: {
    async createHost(position) {
      let host_id = this.next_host_id;
      let host = {
        id: host_id,
        type: "host",
        name: `h${host_id}`,
        label: null,       
        ip: `192.168.1.${host_id}`,
        mac:  (host_id).toString(16).toUpperCase().padStart(12,'0'),
        x: position.x,
        y: position.y
      };
      host.label = host.name
      if (await deployHost(host)) {
        this.nodes.add(host);
        console.log(this.nodes)
        this.next_host_id++;
      } else {
        throw "Could not create host " + host_id
      }
    },
    handleDrop(event) {
      event.preventDefault();
      if (1) {
        this.createHost(this.network.DOMtoCanvas({x: event.clientX, y: event.clientY}))
        console.log(this.network.DOMtoCanvas({x: 0, y: 0}))
        // console.log()
        console.log(event.dataTransfer.getData("text"))
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

</style>