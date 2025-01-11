<template>
  <div
    id="side"
    class="side"
    @dragstart="handleDragStart"
    @keydown.esc="this.$emit('closeAllActiveModes')"
    @keydown.h="this.$emit('toggleShowHosts')"
    @keydown.c="this.$emit('toggleShowControllers')"
    @keydown.e="this.$emit('toggleAddEdgeMode')"
  >
    <p>Mininet Controls</p>
    <button
      id="button-create-link"
      class="button-control-network"
      @click="this.$emit('toggleAddEdgeMode')"
    >
      {{!addEdgeMode ? "Create Link" : "Cancel Add Link"}}
    </button>
    <button
      id="button-delete-selected"
      class="button-control-network"
      @click="this.$emit('deleteSelected')"
    >
      Delete Selected
    </button>
    <button id="button-pingall" class="button-control-network" @click="this.$emit('runPingall')">
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
      alt="host"
      src="@/assets/host.svg"
      draggable="false"
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
    <figure
      id="draggable-controller"
      class="draggable-node"
      draggable="true"
    >
    <img
      alt="controller"
      src="@/assets/controller.svg"
      draggable="false"
    />
    <figcaption>Controller</figcaption>
    </figure>
    <p>Press h to toggle hosts visibility</p>
    <p>Press c to toggle controllers visibility</p>
    <hr>
    <label for="select-topology-style">Select topology style:</label>
    <select v-model="selectedTopology" id="select-topology-style">
      <option value="Single">Single</option>
      <option value="Linear">Linear</option>
      <option value="Tree">Tree</option>
    </select>
    <br>
    <label for="input-topology-ndevices">Select number of nodes:</label>
    <input id="input-topology-ndevices" type="number" v-model="nDevices" min="1" />
    <button class="button-control-network" id="button-create-topology" @click="createTopology()">Create Topology</button>
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
    networkStarted: true,
    addEdgeMode: false,
  },
  data() {
    return {
        sideIsActive: 1,
        selectedTopology: "Single",
        nDevices: 1,
    };
  },
  emits: [
    "toggleAddEdgeMode",
    "networkStart",
    "runPingall",
    "deleteSelected",
    "closeAllActiveModes",
    "toggleShowHosts",
    "toggleShowControllers",
    "createTopology",
  ],
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
    createTopology() {
        console.log("create topology (Side)", event);
        this.$emit("createTopology", {
          selectedTopology: this.selectedTopology,
          nDevices: this.nDevices
        });
    }
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

.side p, figcaption, label {
  color: white;
  font-family: Fira Sans;
  margin: 2.5%;
  padding: 4px;
}

.side select, input {
  color: black;
}

.button-control-network {
  color: white;
  background: var(--oxford-blue);
  border: solid 2px rgba(0, 0, 0, 0.2);
  border-radius: 2px;
  font-size: 11pt;
  font-family: Fira Sans;
  margin: 2.5%;
  padding: 4px;
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
  width: 40px;
  height: auto;
}

.draggable-node > img {
    width: 100%;
}

.draggable-node:hover {
  cursor: grab;
}
</style>
