<template>
  <div id="side" class="side" @dragstart="handleDragStart">
    <p>Mininet Controls</p>
    <button id="button-start-network" class="button-control-network" @click="this.$emit('networkStart')" :disabled="networkStarted">
      Start Network
    </button>
    <button
      id="button-create-link"
      class="button-control-network"
      @click="this.$emit('addEdgeMode')"
    >
      Create Link
    </button>
    <button
      id="button-delete-selected"
      class="button-control-network"
      @click="this.$emit('deleteSelected')"
    >
      Delete Selected Nodes
    </button>
    <button id="button-pingall" class="button-control-network" @click="this.$emit('runPingall')" :disabled="!networkStarted">
      Run Pingall Test
    </button>
    <button id="button-export-network" class="button-control-network">
      Export Network
    </button>
    <figure
      id="draggable-host"
      class="draggable-node"
      draggable="true"
    >
    <img
      id="draggable-host"
      class="draggable-node"
      draggable="true"
      text="host"
      src="@/assets/host.svg"
    />
    <figcaption>Host</figcaption>
    </figure>
    <figure
      id="draggable-switch"
      class="draggable-node"
      draggable="true"
    >
    <img
      alt="switch"
      src="@/assets/switch.svg"
      draggable="false"
    />
    <figcaption>Switch</figcaption>
    </figure>
  </div>
  <button id="button-hide-side" class="button-hide-side" @click="toggleSide()">
    <b>&lt;&lt;</b>
  </button>
</template>

<script>
import { requestStartNetwork } from "../core/api";
export default {
  props: {
    createLinkMode: false,
    networkStarted: false,
  },
  data() {
    return {
        sideIsActive: 1
    };
  },
  emits: ["addEdgeMode", "networkStart", "runPingall", "deleteSelected"],
  methods: {
    toggleSide() {
      if (this.sideIsActive) {
        this.sideIsActive = 0;
        document.getElementById("side").style.display = "none";
        document.getElementById("button-hide-side").style.marginLeft = 0;
        document.getElementById("button-hide-side").innerHTML = "<b>>></b>";
      } else {
        this.sideIsActive = 1;
        document.getElementById("side").style.display = "block";
        document.getElementById("button-hide-side").style.marginLeft = "180px";
        document.getElementById("button-hide-side").innerHTML = "<b><<</b>";
      }
    },
    handleDragStart(event) {
        console.log("dragstart", event);
        event.dataTransfer.setData("text", event.target.id);
    },
  },
};
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0");

.side {
  background: rgba(0, 0, 0, 0.8);
  height: inherit;
  width: 180px;
  position: absolute;
  z-index: 2;
  overflow-x: hidden;
  overflow-y: auto;
}

.side * {
  color: white;
  font-family: Fira Sans;
  margin: 2.5%;
  padding: 4px;
}

.button-control-network {
  background: var(--oxford-blue);
  border: solid 2px rgba(0, 0, 0, 0.2);
  border-radius: 2px;
  font-size: 11pt;
}

.button-control-network:active {
  background: var(--slate-blue);
}

.button-hide-side {
  position: absolute;
  z-index: 4;
  padding: 0;
  margin-left: 180px;
  height: inherit;
  width: 10px;
  font-size: 8pt;
  border: none;
  border-radius: 0 2px 2px 0;
  background: rgba(0, 0, 0, 0.9);
  color: white;
}

.button-hide-side:hover {
  cursor: pointer;
}

.draggable-node {
  width: 70px;
  height: auto;
}

.draggable-node:hover {
  cursor: grab;
}
</style>
