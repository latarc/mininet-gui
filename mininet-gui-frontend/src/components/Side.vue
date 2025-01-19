<template>
  <div
    id="side"
    class="side"
    @dragstart="handleDragStart"
    @keydown.esc="this.$emit('closeAllActiveModes')"
    @keydown.h="this.$emit('toggleShowHosts')"
    @keydown.c="this.$emit('toggleShowControllers')"
    @keydown.e="this.$emit('toggleAddEdgeMode')"
    @keydown.d="this.$emit('deleteSelected')"
    @keydown.delete="this.$emit('deleteSelected')"
    @keydown.ctrl.a.prevent="this.$emit('doSelectAll')"
  >
    <p>Mininet Controls</p>
    <button class="button-control-network" id="button-create-topology" @click="createTopology()">Generate Topology</button>
    <button class="button-control-network" id="button-reset-topology" @click="this.$emit('resetTopology')">Reset Topology</button>
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
    <button class="button-control-network" id="button-export-topology" @click="this.$emit('exportTopology')">Export Topology (JSON)</button>
    <button class="button-control-network" id="button-import-topology" @click="openFileDialog">Import Topology (JSON)</button>

    <!-- Hidden file input -->
    <input 
      type="file" 
      id="fileInput" 
      accept=".json" 
      style="display: none" 
      @change="handleFileUpload"
    />

    <figure id="draggable-host" class="draggable-node" draggable="true">
      <img alt="host" src="@/assets/host.svg" draggable="false" />
      <figcaption>Host</figcaption>
    </figure>
    <figure id="draggable-switch" class="draggable-node" draggable="true">
      <img alt="switch" src="@/assets/switch.svg" draggable="false" />
      <figcaption>Switch</figcaption>
    </figure>
    <figure id="draggable-controller" class="draggable-node" draggable="true">
      <img alt="controller" src="@/assets/controller.svg" draggable="false" />
      <figcaption>Controller</figcaption>
    </figure>
    <br>
    <p><u>Hotkeys</u></p>
    <p>Press d to delete selected nodes</p>
    <p>Press ctrl + a to select all nodes</p>
    <p>Press h to toggle hosts visibility</p>
    <p>Press c to toggle controllers visibility</p>
  </div>
  <button id="button-hide-side" class="button-hide-side" @click="toggleSide()">
    <b>&lt;&lt;</b>
  </button>
</template>

<script>

export default {
  props: {
    createLinkMode: false,
    networkStarted: true,
    addEdgeMode: false,
  },
  data() {
    return {
      sideIsActive: 1,
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
    "resetTopology",
    "exportTopology",
    "importTopology",
    "doSelectAll",
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
      this.$emit("createTopology", {
        selectedTopology: this.selectedTopology,
        nDevices: this.nDevices
      });
    },
    openFileDialog() {
      document.getElementById("fileInput").click();
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file){
        this.$emit("importTopology", file);
      }
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
