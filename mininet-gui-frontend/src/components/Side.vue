<template>
  <div
    id="side"
    class="side"
    tabindex="0"
    @dragstart="handleDragStart"
    @keydown.esc="$emit('closeAllActiveModes')"
    @keydown.h="$emit('toggleShowHosts')"
    @keydown.c="$emit('toggleShowControllers')"
    @keydown.e="$emit('toggleAddEdgeMode')"
    @keydown.d="$emit('deleteSelected')"
    @keydown.delete="$emit('deleteSelected')"
    @keydown.ctrl.a.prevent="$emit('doSelectAll')"
  >
    <!-- Topology Controls Group -->
    <div class="sidebar-group">
      <h2>Topology Controls</h2>
      <button class="button-control-network" id="button-create-topology" @click="createTopology()">
        <span class="material-symbols-outlined">scatter_plot</span>
        Generate Topology
      </button>
      <button class="button-control-network" id="button-reset-topology" @click="$emit('resetTopology')">
        <span class="material-symbols-outlined">restart_alt</span>
        Reset Topology
      </button>
    </div>

    <!-- Link & Delete Actions Group -->
    <div class="sidebar-group">
      <h2>Actions</h2>
      <button id="button-create-link" class="button-control-network" @click="$emit('toggleAddEdgeMode')">
        <span class="material-symbols-outlined">link</span>
        {{ !addEdgeMode ? "Create Link" : "Cancel Add Link" }}
      </button>
      <button id="button-delete-selected" class="button-control-network" @click="$emit('deleteSelected')">
        <span class="material-symbols-outlined">delete</span>
        Delete Selected
      </button>
      <button id="button-pingall" class="button-control-network" @click="$emit('runPingall')">
        <span class="material-symbols-outlined">network_check</span>
        Run Pingall Test
      </button>
    </div>

    <!-- Export/Import Controls Group -->
    <div class="sidebar-group">
      <h2>Export/Import</h2>
      <button class="button-control-network" id="button-export-topology" @click="$emit('exportTopology')">
        <span class="material-symbols-outlined">upload_file</span>
        Export Topology (JSON)
      </button>
      <button class="button-control-network" id="button-import-topology" @click="openFileDialog">
        <span class="material-symbols-outlined">download</span>
        Import Topology (JSON)
      </button>
      <button class="button-control-network" id="button-export-script" @click="$emit('exportMininetScript')">
        <span class="material-symbols-outlined">code</span>
        Export Mininet Script
      </button>
      <!-- Hidden file input -->
      <input 
        type="file" 
        id="fileInput" 
        accept=".json" 
        style="display: none" 
        @change="handleFileUpload"
      />
    </div>

    <!-- Draggable Nodes Group -->
    <div class="sidebar-group">
      <h2>Nodes Palette</h2>
      <div class="draggable-container">
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
      </div>
    </div>

    <!-- Hotkeys Help Group -->
    <div class="sidebar-group hotkeys">
      <h2>Hotkeys</h2>
      <p><strong>d</strong>: Delete selected nodes</p>
      <p><strong>ctrl + a</strong>: Select all nodes</p>
      <p><strong>h</strong>: Toggle hosts visibility</p>
      <p><strong>c</strong>: Toggle controllers visibility</p>
    </div>
  </div>

  <button id="button-hide-side" class="button-hide-side" @click="toggleSide()">
    <span class="material-symbols-outlined">chevron_left</span>
  </button>
</template>

<script>
export default {
  props: {
    createLinkMode: { type: Boolean, default: false },
    networkStarted: { type: Boolean, default: true },
    addEdgeMode: { type: Boolean, default: false },
  },
  data() {
    return {
      sideIsActive: true,
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
    "exportMininetScript",
    "exportTopology",
    "importTopology",
    "doSelectAll",
  ],
  methods: {
    toggleSide() {
      this.sideIsActive = !this.sideIsActive;
      const side = document.getElementById("side");
      const button = document.getElementById("button-hide-side");
      if (!this.sideIsActive) {
        side.style.display = "none";
        button.style.marginLeft = "0";
        button.innerHTML = '<span class="material-symbols-outlined">chevron_right</span>';
      } else {
        side.style.display = "block";
        button.style.marginLeft = "200px";
        button.innerHTML = '<span class="material-symbols-outlined">chevron_left</span>';
      }
    },
    handleDragStart(event) {
      console.log("dragstart", event);
      event.dataTransfer.setData("text", event.target.id);
    },
    createTopology() {
      this.$emit("createTopology", {
        selectedTopology: this.selectedTopology,
        nDevices: this.nDevices,
      });
    },
    openFileDialog() {
      document.getElementById("fileInput").click();
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.$emit("importTopology", file);
      }
    },
  },
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0");

.side {
  background-color: #1e1e1e;
  height: 75vh;
  width: 200px;
  position: absolute;
  z-index: 2;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box;

  /* SCROLLBAR FOR FIREFOX */
  scrollbar-width: thin;
  scrollbar-color: #007acc #1e1e1e;
}

/* SCROLLBAR FOR WEBKIT (Chrome, Edge, Safari) */
.side::-webkit-scrollbar {
  width: 8px;
}
.side::-webkit-scrollbar-track {
  background: #1e1e1e;
}
.side::-webkit-scrollbar-thumb {
  background-color: #007acc;
  border-radius: 4px;
}
.side::-webkit-scrollbar-thumb:hover {
  background-color: #005a9e;
}

.side h2 {
  color: #cccccc;
  font-family: 'Fira Sans', sans-serif;
  margin: 10px 5px;
  font-size: 14pt;
  border-bottom: 1px solid #333;
  padding-bottom: 5px;
}

.side p,
figcaption {
  color: #cccccc;
  font-family: 'Fira Sans', sans-serif;
  margin: 5px 5px;
  padding: 2px;
  font-size: 10pt;
}

.side input,
.side select {
  color: #000;
}

.sidebar-group {
  margin-bottom: 15px;
}

.button-control-network {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #cccccc;
  background-color: #2d2d2d;
  border: solid 1px #333;
  border-radius: 4px;
  font-size: 10pt;
  font-family: 'Fira Sans', sans-serif;
  margin: 5px;
  padding: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.button-control-network:hover {
  background-color: #3e3e3e;
}

.button-control-network:active {
  background-color: #007acc;
}

.button-hide-side {
  position: absolute;
  z-index: 4;
  padding: 0;
  margin-left: 200px;
  height: 75vh;
  width: 24px;
  font-size: 14pt;
  border: none;
  border-radius: 0 4px 4px 0;
  background-color: #1e1e1e;
  color: #cccccc;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.button-hide-side:hover {
  background-color: #2d2d2d;
}

.draggable-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 5px;
  gap: 10px;
}

.draggable-node {
  width: 40px;
  text-align: center;
  padding: 5px;
}

.draggable-node > img {
  width: 100%;
  filter: brightness(0) invert(1);
}

.draggable-node figcaption {
  color: #cccccc;
  font-size: 9pt;
  margin-top: 4px;
}

.draggable-node:hover {
  cursor: grab;
  opacity: 0.9;
}

.hotkeys p {
  font-size: 9pt;
  margin: 3px 5px;
}
</style>
