<template>
  <div id="network-graph"></div>
</template>

<script>
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

import { deployNode } from '../core/api';

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
    createHost() {
      // Generate unique default values for the node
      // Create the node object
      let host_id = this.next_host_id++;
      return {
        node_id: host_id,
        node_type: "host",
        name: `h${host_id}`,
        ip: `192.168.1.${host_id}`,
        mac:  (host_id).toString(16).toUpperCase().padStart(12,'0'),
      }
    }
  },
  mounted() {
    console.log("teste")
    const container = document.getElementById('network-graph');
    const data = {
      nodes: this.nodes,
      edges: this.edges
    };
    const options = {
      edges: {
        font: {
          size: 12,
        },
        widthConstraint: {
          maximum: 90,
        },
      },
      nodes: {
        shape: "box",
        margin: 10,
        widthConstraint: {
          maximum: 200,
        },
      },
      physics: {
        enabled: false,
      },
      
      // width: '70%',
      // height: '20px'
    };
    this.network = new Network(container, data, options);

    this.network.on('click', async (event) => {
      // Check if the click was on an empty area of the graph
      if (event.nodes.length === 0) {
        let node = this.createHost(); // TODO: Change node_type accordingly
        // Deploy node in backend via API
        if (await deployNode(node)) {
          // Add the node to the graph if the API returns an OK
          node.label = node.name
          this.nodes.add(node);
        }
      }
      console.log("foo")
    });
  },
  // Add methods for adding and removing edges here
};
</script>
