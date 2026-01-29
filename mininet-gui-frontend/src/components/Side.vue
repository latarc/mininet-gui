<template>
  <div
    id="side"
    :class="['side', { collapsed: !sideIsActive }]"
    class="flex h-full w-[80vw] min-w-[220px] max-w-[320px] flex-col bg-[#1e1e1e] text-[#cccccc] outline-none sm:w-[60vw] lg:w-[280px]"
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
    <div class="flex w-full flex-col items-center gap-2 p-3">
      <img
        src="@/assets/logo-mininet-gui.png"
        alt="Mininet GUI"
        class="h-10 w-auto object-contain"
      />
      <button
        id="button-hide-side"
        class="icon-button"
        type="button"
        @click="toggleSide()"
        aria-label="Toggle sidebar"
      >
        <span class="material-symbols-outlined">{{ sideIsActive ? "menu_open" : "menu" }}</span>
      </button>
    </div>
    <div class="w-full border-t border-[#333]" aria-hidden="true"></div>
    <div class="side-scroll flex flex-col gap-4 overflow-x-hidden overflow-y-auto p-3">
    <!-- Topology Controls Group -->
    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b border-[#333] pb-2 text-[13px] font-semibold tracking-wide text-[#cccccc]">
        Topology Controls
      </h2>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        id="button-create-topology"
        @click="createTopology()"
      >
        <span class="material-symbols-outlined">scatter_plot</span>
        <span class="label">Generate Topology</span>
      </button>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        id="button-reset-topology"
        @click="$emit('resetTopology')"
      >
        <span class="material-symbols-outlined">restart_alt</span>
        <span class="label">Reset Topology</span>
      </button>
    </div>

    <!-- Link & Delete Actions Group -->
    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b border-[#333] pb-2 text-[13px] font-semibold tracking-wide text-[#cccccc]">
        Actions
      </h2>
      <button
        id="button-create-link"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :class="addEdgeMode ? 'border-[#007acc] bg-[#0b2b3b] text-[#e6f2ff] ring-1 ring-[#007acc]' : ''"
        @click="$emit('toggleAddEdgeMode')"
      >
        <span class="material-symbols-outlined">link</span>
        <span class="label">{{ !addEdgeMode ? "Create Link" : "Cancel Add Link" }}</span>
      </button>
      <button
        id="button-delete-selected"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        @click="$emit('deleteSelected')"
      >
        <span class="material-symbols-outlined">delete</span>
        <span class="label">Delete Selected</span>
      </button>
      <button
        id="button-pingall"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :class="pingallRunning ? 'opacity-60 cursor-not-allowed' : ''"
        :disabled="pingallRunning"
        @click="$emit('runPingall')"
      >
        <span class="material-symbols-outlined">network_check</span>
        <span class="label">{{ pingallRunning ? "Pingall running..." : "Run Pingall Test" }}</span>
      </button>
      <button
        id="button-sniffer"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :class="snifferActive ? 'border-[#007acc] bg-[#0b2b3b] text-[#e6f2ff] ring-1 ring-[#007acc]' : ''"
        @click="$emit('toggleSniffer')"
      >
        <span class="material-symbols-outlined">radar</span>
        <span class="label">{{ snifferActive ? "Stop Sniffer" : "Start Sniffer" }}</span>
      </button>
      <button
        id="button-export-sniffer"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        @click="$emit('exportSniffer')"
      >
        <span class="material-symbols-outlined">download</span>
        <span class="label">Export Sniffer (PCAP)</span>
      </button>
    </div>

    <!-- Export/Import Controls Group -->
    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b border-[#333] pb-2 text-[13px] font-semibold tracking-wide text-[#cccccc]">
        Export/Import
      </h2>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        id="button-export-topology"
        @click="$emit('exportTopology')"
      >
        <span class="material-symbols-outlined">upload_file</span>
        <span class="label">Export Topology (JSON)</span>
      </button>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        id="button-import-topology"
        @click="openFileDialog"
      >
        <span class="material-symbols-outlined">download</span>
        <span class="label">Import Topology (JSON)</span>
      </button>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        id="button-export-script"
        @click="$emit('exportMininetScript')"
      >
        <span class="material-symbols-outlined">code</span>
        <span class="label">Export Mininet Script</span>
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
    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b border-[#333] pb-2 text-[13px] font-semibold tracking-wide text-[#cccccc]">
        Nodes Palette
      </h2>
      <div class="draggable-container flex flex-col items-center gap-3 py-2">
        <figure
          id="draggable-host"
          class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
          draggable="true"
        >
          <img alt="host" class="h-10 w-10" src="@/assets/host.svg" draggable="false" />
          <figcaption class="text-[11px] text-[#cccccc]">Host</figcaption>
        </figure>
        <figure
          id="draggable-switch"
          class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
          draggable="true"
        >
          <img alt="switch" class="h-10 w-10" src="@/assets/switch.svg" draggable="false" />
          <figcaption class="text-[11px] text-[#cccccc]">Switch</figcaption>
        </figure>
        <figure
          id="draggable-controller"
          class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
          draggable="true"
        >
          <img
            alt="controller"
            class="h-10 w-10"
            src="@/assets/controller.svg"
            draggable="false"
          />
          <figcaption class="text-[11px] text-[#cccccc]">Controller</figcaption>
        </figure>
      </div>
    </div>

    <!-- Hotkeys Help Group
    <div class="sidebar-group hotkeys">
      <h2>Hotkeys</h2>
      <p><strong>d</strong>: Delete selected nodes</p>
      <p><strong>ctrl + a</strong>: Select all nodes</p>
      <p><strong>h</strong>: Toggle hosts visibility</p>
      <p><strong>c</strong>: Toggle controllers visibility</p>
    </div> -->
    </div>
  </div>

</template>

<script>
export default {
  props: {
    createLinkMode: { type: Boolean, default: false },
    networkStarted: { type: Boolean, default: true },
    addEdgeMode: { type: Boolean, default: false },
    snifferActive: { type: Boolean, default: false },
    pingallRunning: { type: Boolean, default: false },
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
    "toggleSniffer",
    "exportSniffer",
    "toggleSidebar",
  ],
  methods: {
    toggleSide() {
      this.sideIsActive = !this.sideIsActive;
      this.$emit("toggleSidebar", this.sideIsActive);
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
  position: relative;
  z-index: 2;
  box-sizing: border-box;
}

.side-scroll {
  scrollbar-width: thin;
  scrollbar-color: #007acc #1e1e1e;
}

.side.collapsed {
  width: 64px !important;
  min-width: 64px !important;
  max-width: 64px !important;
}

.side.collapsed .label,
.side.collapsed h2,
.side.collapsed figcaption {
  display: none;
}

.side.collapsed .button-control-network {
  width: 40px;
  height: 40px;
  padding: 0;
  justify-content: center;
}

.button-control-network {
  width: 100%;
  box-sizing: border-box;
}

.side.collapsed .button-control-network .material-symbols-outlined {
  font-size: 20px;
}

.side.collapsed .draggable-node {
  width: 36px;
}

.side.collapsed img {
  max-height: 40px;
}

.icon-button {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #cccccc;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.icon-button:hover {
  background-color: #2d2d2d;
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

.side input,
.side select {
  color: #000;
}

.draggable-node > img {
  width: 100%;
  filter: brightness(0) invert(1);
}

.draggable-node:hover {
  cursor: grab;
  opacity: 0.9;
}
</style>
