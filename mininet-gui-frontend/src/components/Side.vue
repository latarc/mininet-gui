<template>
  <div
    id="side"
    :class="['side', { collapsed: !sideIsActive }]"
    class="flex h-full w-[80vw] min-w-[220px] max-w-[320px] flex-col bg-[#1e1e1e] text-[#cccccc] outline-none sm:w-[60vw] lg:w-[280px]"
    tabindex="0"
    @keydown.esc="$emit('closeAllActiveModes')"
    @keydown.h="$emit('toggleShowHosts')"
    @keydown.c="$emit('toggleShowControllers')"
    @keydown.e="$emit('toggleAddEdgeMode')"
    @keydown.d="$emit('deleteSelected')"
    @keydown.delete="$emit('deleteSelected')"
    @keydown.ctrl.a.prevent="$emit('doSelectAll')"
  >
    <div
      class="flex w-full flex-col items-center gap-2"
      :class="sideIsActive ? 'p-3' : 'py-3 px-0'"
    >
      <div class="tooltip-container">
        <button
          id="button-hide-side"
          class="icon-button"
          type="button"
          @click="toggleSide()"
          aria-label="Toggle sidebar"
          :class="!sideIsActive ? 'w-full rounded-none' : ''"
          @mouseenter="handleTooltipMouseEnter($event, 'Toggle sidebar')"
          @mousemove="handleTooltipMouseMove"
          @mouseleave="hideTooltip"
        >
          <span class="material-symbols-outlined">{{ sideIsActive ? "menu_open" : "menu" }}</span>
        </button>
        <div v-if="tooltip.visible" class="sidebar-tooltip" :style="tooltipStyle">{{ tooltip.text }}</div>
      </div>
    </div>
    <div class="w-full border-t border-[#333]" aria-hidden="true"></div>
    <div class="side-scroll flex flex-1 flex-col gap-4 overflow-x-hidden overflow-y-auto p-3">
    <!-- Core Actions Group -->
    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b border-[#333] pb-2 text-[13px] font-semibold tracking-wide text-[#cccccc]">
        Actions
      </h2>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        id="button-create-topology"
        :disabled="!networkConnected"
        @mouseenter="handleTooltipMouseEnter($event, 'Generate topology')"
        @mousemove="handleTooltipMouseMove($event)"
        @mouseleave="hideTooltip"
        @click="createTopology()"
      >
        <span class="material-symbols-outlined">scatter_plot</span>
        <span class="label">Generate Topology</span>
      </button>
      <button
        id="button-pingall"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :class="pingallRunning ? 'opacity-60 cursor-not-allowed' : ''"
        :disabled="!networkConnected || pingallRunning"
        data-tooltip="Run pingall"
        @mouseenter="handleTooltipMouseEnter($event, 'Run pingall')"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('runPingall')"
      >
        <span class="material-symbols-outlined">network_check</span>
        <span class="label">{{ pingallRunning ? "Pingall running..." : "Run Pingall Test" }}</span>
      </button>
      <button
        id="button-iperf"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :class="iperfRunning ? 'opacity-60 cursor-not-allowed' : ''"
        :disabled="!networkConnected || iperfRunning"
        data-tooltip="Run iperf test"
        @mouseenter="handleTooltipMouseEnter($event, 'Run iperf test')"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('runIperf')"
      >
        <span class="material-symbols-outlined">speed</span>
        <span class="label">{{ iperfRunning ? "Iperf running..." : "Run Iperf" }}</span>
      </button>
      <button
        id="button-create-link"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :class="addEdgeMode ? 'border-[#007acc] bg-[#0b2b3b] text-[#e6f2ff] ring-1 ring-[#007acc]' : ''"
        :disabled="!networkConnected"
        data-tooltip="Toggle connect mode"
        @mouseenter="handleTooltipMouseEnter($event, addEdgeMode ? 'Cancel connect mode' : 'Toggle connect mode')"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('toggleAddEdgeMode')"
      >
        <span class="material-symbols-outlined">link</span>
        <span class="label">{{ !addEdgeMode ? "Connect Nodes" : "Cancel Connect" }}</span>
      </button>
      <button
        id="button-delete-selected"
        class="button-control-network flex items-center gap-2 rounded-md border border-[#333] bg-[#2d2d2d] px-2 py-1.5 text-[12px] font-medium text-[#cccccc] transition-colors hover:bg-[#3e3e3e] active:bg-[#007acc]"
        :disabled="!networkConnected"
        data-tooltip="Delete selection"
        @mouseenter="handleTooltipMouseEnter($event, 'Delete selection')"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('deleteSelected')"
      >
        <span class="material-symbols-outlined">delete</span>
        <span class="label">Delete Selected</span>
      </button>
    </div>

    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b border-[#333] pb-2 text-[13px] font-semibold tracking-wide text-[#cccccc]">
        Nodes Palette
      </h2>
      <div class="draggable-container flex flex-col items-center gap-4 py-2">
        <div class="palette-group w-full">
          <div class="palette-title text-[11px] uppercase tracking-wide text-[#9b9b9b]">Main Nodes</div>
          <div class="palette-items flex flex-col items-center gap-3 pt-2">
            <figure
              id="draggable-host"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="Host"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="host" class="h-10 w-10" src="@/assets/light-host.svg" draggable="false" />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">Host</figcaption>
            </figure>
            <figure
              id="draggable-switch"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="Switch"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch" class="h-10 w-10" src="@/assets/light-switch.svg" draggable="false" />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">Switch</figcaption>
            </figure>
            <figure
              id="draggable-controller-default"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="Controller"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img
                alt="controller"
                class="h-10 w-10"
                src="@/assets/light-controller.svg"
                draggable="false"
              />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">Controller</figcaption>
            </figure>
            <figure
              id="draggable-nat"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="NAT"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img
                alt="nat"
                class="h-10 w-10"
                src="@/assets/light-nat.svg"
                draggable="false"
              />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">NAT</figcaption>
            </figure>
            <figure
              id="draggable-router"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="Router"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="router" class="h-10 w-10" src="@/assets/light-router.svg" draggable="false" />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">Router</figcaption>
            </figure>
          </div>
        </div>
        <div v-if="showSpecialSwitches" class="palette-group w-full">
          <div class="palette-title text-[11px] uppercase tracking-wide text-[#9b9b9b]">Special Switches</div>
          <div class="palette-items flex flex-col items-center gap-3 pt-2">
            <figure
              id="draggable-switch-ovs"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="OVS Switch"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch ovs" class="h-10 w-10" src="@/assets/light-switch-ovs.svg" draggable="false" />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">OVS Switch</figcaption>
            </figure>
            <figure
              id="draggable-switch-user"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="User Switch"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch user" class="h-10 w-10" src="@/assets/light-switch-user.svg" draggable="false" />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">User Switch</figcaption>
            </figure>
            <figure
              id="draggable-switch-ovsbridge"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="OVS Bridge"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch ovsbridge" class="h-10 w-10" src="@/assets/light-switch-ovsbridge.svg" draggable="false" />
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">OVS Bridge</figcaption>
            </figure>
          </div>
        </div>
        <div v-if="showSpecialControllers" class="palette-group w-full">
          <div class="palette-title text-[11px] uppercase tracking-wide text-[#9b9b9b]">Special Controllers</div>
          <div class="palette-items flex flex-col items-center gap-3 pt-2">
            <figure
              id="draggable-controller-remote"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="Remote Controller"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <div class="controller-icon">
                <img
                  alt="controller remote"
                  class="h-10 w-10"
                  src="@/assets/light-controller.svg"
                  draggable="false"
                />
                <span class="controller-badge controller-badge--remote">Rem</span>
              </div>
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">Remote</figcaption>
            </figure>
            <figure
              id="draggable-controller-ryu"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="Ryu Controller"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <div class="controller-icon">
                <img
                  alt="controller ryu"
                  class="h-10 w-10"
                  src="@/assets/light-controller.svg"
                  draggable="false"
                />
                <span class="controller-badge">Ryu</span>
              </div>
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">Ryu</figcaption>
            </figure>
            <figure
              id="draggable-controller-nox"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              data-tooltip="NOX Controller"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <div class="controller-icon">
                <img
                  alt="controller nox"
                  class="h-10 w-10"
                  src="@/assets/light-controller.svg"
                  draggable="false"
                />
                <span class="controller-badge">NOX</span>
              </div>
              <figcaption class="text-[11px] text-[#cccccc] whitespace-nowrap">NOX</figcaption>
            </figure>
          </div>
        </div>
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
    networkStarted: { type: Boolean, default: true },
    networkConnected: { type: Boolean, default: true },
    showSpecialSwitches: { type: Boolean, default: true },
    showSpecialControllers: { type: Boolean, default: true },
    addEdgeMode: { type: Boolean, default: false },
    pingallRunning: { type: Boolean, default: false },
    iperfRunning: { type: Boolean, default: false },
  },
  data() {
    return {
      sideIsActive: true,
      tooltip: {
        visible: false,
        text: "",
        top: 0,
        left: 0,
      },
    };
  },
  computed: {
    tooltipStyle() {
      return {
        top: `${this.tooltip.top}px`,
        left: `${this.tooltip.left}px`,
      };
    },
  },
  emits: [
    "toggleAddEdgeMode",
    "runPingall",
    "runIperf",
    "deleteSelected",
    "closeAllActiveModes",
    "toggleShowHosts",
    "toggleShowControllers",
    "createTopology",
    "doSelectAll",
    "toggleSidebar",
  ],
  methods: {
    toggleSide() {
      this.sideIsActive = !this.sideIsActive;
      this.$emit("toggleSidebar", this.sideIsActive);
    },
    handleDragStart(event) {
      const id = event.currentTarget?.id || event.target?.id;
      if (!id) return;
      event.dataTransfer.setData("text/plain", id);
      event.dataTransfer.setData("text", id);
    },
    createTopology() {
      this.$emit("createTopology", {
        selectedTopology: this.selectedTopology,
        nDevices: this.nDevices,
      });
    },
    shouldShowTooltip() {
      return !this.sideIsActive;
    },
    handleTooltipMouseEnter(event, text) {
      if (!this.shouldShowTooltip()) {
        return;
      }
      const tooltipText =
        text ||
        event.currentTarget?.dataset?.tooltip ||
        event.target?.dataset?.tooltip ||
        "";
      if (!tooltipText) {
        this.hideTooltip();
        return;
      }
      this.tooltip.text = tooltipText;
      this.tooltip.visible = true;
      this.updateTooltipPosition(event);
    },
    handleTooltipMouseMove(event) {
      if (!this.tooltip.visible) return;
      this.updateTooltipPosition(event);
    },
    hideTooltip() {
      this.tooltip.visible = false;
    },
    updateTooltipPosition(event) {
      const offset = 16;
      const clientX = event?.clientX ?? 0;
      const clientY = event?.clientY ?? 0;
      this.tooltip.top = clientY + offset;
      this.tooltip.left = clientX + offset;
    },
  },
  watch: {
    sideIsActive(value) {
      if (value) {
        this.hideTooltip();
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

.controller-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.controller-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: rgba(0, 122, 204, 0.9);
  color: #ffffff;
  font-size: 8px;
  font-weight: 700;
  padding: 1px 3px;
  border-radius: 4px;
  line-height: 1;
}

.controller-badge--remote {
  background: #007acc;
  color: #ffffff;
  padding: 1px 3px;
  border-radius: 0;
}


.side.collapsed {
  width: 64px !important;
  min-width: 64px !important;
  max-width: 64px !important;
}

.side.collapsed .side-scroll {
  scrollbar-width: none;
}

.side.collapsed .side-scroll::-webkit-scrollbar {
  display: none;
}

.side.collapsed .label,
.side.collapsed h2,
.side.collapsed figcaption {
  display: none;
}

.side.collapsed .palette-title {
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

.sidebar-tooltip {
  position: fixed;
  pointer-events: none;
  background: #111;
  color: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  border: 1px solid #2f2f2f;
  white-space: nowrap;
  z-index: 30;
  transition: opacity 0.1s ease;
}

.button-control-network:disabled {
  opacity: 0.45;
  cursor: not-allowed;
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

.collapsed-hint {
  position: relative;
  padding-top: 14px;
}

.collapsed-hint::before {
  content: "";
  position: absolute;
  left: 12px;
  right: 12px;
  top: 4px;
  height: 10px;
  background: linear-gradient(to bottom, rgba(0, 122, 204, 0.4), rgba(0, 122, 204, 0));
  border-radius: 999px;
  pointer-events: none;
}

.icon-button {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  color: #cccccc;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  position: relative;
}

.icon-button:hover {
  background-color: #2d2d2d;
}

/* SCROLLBAR FOR WEBKIT (Chrome, Edge, Safari) */
.side-scroll::-webkit-scrollbar {
  width: 8px;
}

.side-scroll::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.side-scroll::-webkit-scrollbar-thumb {
  background-color: #007acc;
  border-radius: 4px;
}

.side-scroll::-webkit-scrollbar-thumb:hover {
  background-color: #005a9e;
}

.side input,
.side select {
  color: #000;
}

.side select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.side select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.draggable-node > img {
  width: 100%;
}

.draggable-node:hover {
  cursor: grab;
  opacity: 0.9;
}

</style>
