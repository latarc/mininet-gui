<template>
  <div id="network-graph"></div>
</template>

<script>
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

// import { DataSet, Network } from "vis-network";
import { createNode } from './api';
import { createNodeObject } from './node';

export default {
  name: 'NetworkGraph',
  data() {
    return {
      network: null,
      nodes: new DataSet(),
      edges: new DataSet()
    };
  },
  mounted() {
    console.log("teste")
    const container = document.getElementById('network-graph');
    const data = {
      nodes: this.nodes,
      edges: this.edges
    };
    const options = {
      width: '800px',
      height: '600px'
    };
    this.network = new Network(container, data, options);

    this.network.on('click', async (event) => {
      // Check if the click was on an empty area of the graph
      if (event.nodes.length === 0) {
        // Create the node object
        const node = createNodeObject();
        // Send the node data to the backend for deployment
        if (await createNode(node)) {
          // Add the node to the graph if the API returns an OK
          this.nodes.add(node);
        }
      }
      console.log("foo")
    });
  },
  // Add methods for adding and removing edges here
};
</script>

<style>
#network-graph {
  background-color: white;
}
</style>