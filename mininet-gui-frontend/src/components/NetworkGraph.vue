<script setup>
  import { Network } from 'vis-network';
  import { DataSet } from 'vis-data';
  
  import { getNodes, deployHost } from '../core/api';
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
  data() {
    return {
      next_host_id: 1,
      network: null,
      nodes: new DataSet(),
      edges: new DataSet()
    };
  },
  methods: {
    async createHost(position) {
      let host_id = this.next_host_id++;
      let host = {
        node_id: host_id,
        node_type: "host",
        name: `h${host_id}`,
        ip: `192.168.1.${host_id}`,
        mac:  (host_id).toString(16).toUpperCase().padStart(12,'0'),
        x: position.x,
        y: position.y
      };
      if (await deployHost(host)) {
        host.label = host.name
        this.nodes.add(host);
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
  beforeCreate() {
    this.nodes = getNodes();
  },
  mounted() {
    console.log("teste")
    const container = document.getElementById('network-graph');
    console.log(this.nodes)
    const data = {
      nodes: this.nodes,
      edges: this.edges
    };

    this.network = new Network(container, data, options);

  },
  // Add methods for adding and removing edges here
};
</script>


<style>

.network-graph {
    /* margin-top:auto; */
    /* position: relative; */
    background-color: white;
    height: inherit;
    width: inherit;
    position: absolute;
    z-index: 1;
}

</style>