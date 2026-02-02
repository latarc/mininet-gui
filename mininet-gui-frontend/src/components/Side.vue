<template>
  <div
    id="side"
    :class="['side', themeClass, { collapsed: !sideIsActive }]"
    class="flex h-full w-[80vw] min-w-[220px] max-w-[320px] flex-col outline-none sm:w-[60vw] lg:w-[280px]"
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
          :aria-label="$t('side.toggleSidebar')"
          :class="!sideIsActive ? 'w-full rounded-none' : ''"
          @mouseenter="handleTooltipMouseEnter($event, $t('side.toggleSidebar'))"
          @mousemove="handleTooltipMouseMove"
          @mouseleave="hideTooltip"
        >
          <span class="material-symbols-outlined">{{ sideIsActive ? "menu_open" : "menu" }}</span>
        </button>
        <div v-if="tooltip.visible" class="sidebar-tooltip" :style="tooltipStyle">{{ tooltip.text }}</div>
      </div>
    </div>
    <div class="sidebar-divider w-full border-t" aria-hidden="true"></div>
    <div class="side-scroll flex flex-1 flex-col gap-4 overflow-x-hidden overflow-y-auto p-3">
    <!-- Core Actions Group -->
    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b pb-2 text-[13px] font-semibold tracking-wide">
        {{ $t("side.actions") }}
      </h2>
      <button
        class="button-control-network flex items-center gap-2 rounded-md border px-2 py-1.5 text-[12px] font-medium transition-colors"
        id="button-create-topology"
        :disabled="!networkConnected"
        @mouseenter="handleTooltipMouseEnter($event, $t('side.generateTopology'))"
        @mousemove="handleTooltipMouseMove($event)"
        @mouseleave="hideTooltip"
        @click="createTopology()"
      >
        <span class="material-symbols-outlined">scatter_plot</span>
        <span class="label">{{ $t("side.generateTopology") }}</span>
      </button>
      <button
        id="button-pingall"
        class="button-control-network flex items-center gap-2 rounded-md border px-2 py-1.5 text-[12px] font-medium transition-colors"
        :class="pingallRunning ? 'opacity-60 cursor-not-allowed' : ''"
        :disabled="!networkConnected || pingallRunning"
        :data-tooltip="$t('side.runPingall')"
        @mouseenter="handleTooltipMouseEnter($event, $t('side.runPingall'))"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('runPingall')"
      >
        <span class="material-symbols-outlined">network_check</span>
        <span class="label">{{ pingallRunning ? $t("side.pingallRunning") : $t("side.runPingallTest") }}</span>
      </button>
      <button
        id="button-iperf"
        class="button-control-network flex items-center gap-2 rounded-md border px-2 py-1.5 text-[12px] font-medium transition-colors"
        :class="iperfRunning ? 'opacity-60 cursor-not-allowed' : ''"
        :disabled="!networkConnected || iperfRunning"
        :data-tooltip="$t('side.runIperf')"
        @mouseenter="handleTooltipMouseEnter($event, $t('side.runIperf'))"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('runIperf')"
      >
        <span class="material-symbols-outlined">speed</span>
        <span class="label">{{ iperfRunning ? $t("side.iperfRunning") : $t("side.runIperf") }}</span>
      </button>
      <button
        id="button-create-link"
        class="button-control-network flex items-center gap-2 rounded-md border px-2 py-1.5 text-[12px] font-medium transition-colors"
        :class="addEdgeMode ? 'border-[#007acc] bg-[#0b2b3b] text-[#e6f2ff] ring-1 ring-[#007acc]' : ''"
        :disabled="!networkConnected"
        :data-tooltip="$t('side.toggleConnectMode')"
        @mouseenter="handleTooltipMouseEnter($event, addEdgeMode ? $t('side.cancelConnectMode') : $t('side.toggleConnectMode'))"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('toggleAddEdgeMode')"
      >
        <span class="material-symbols-outlined">link</span>
        <span class="label">{{ !addEdgeMode ? $t("side.connectNodes") : $t("side.cancelConnect") }}</span>
      </button>
      <button
        id="button-delete-selected"
        class="button-control-network flex items-center gap-2 rounded-md border px-2 py-1.5 text-[12px] font-medium transition-colors"
        :disabled="!networkConnected"
        :data-tooltip="$t('side.deleteSelection')"
        @mouseenter="handleTooltipMouseEnter($event, $t('side.deleteSelection'))"
        @mousemove="handleTooltipMouseMove"
        @mouseleave="hideTooltip"
        @click="$emit('deleteSelected')"
      >
        <span class="material-symbols-outlined">delete</span>
        <span class="label">{{ $t("side.deleteSelected") }}</span>
      </button>
    </div>

    <div class="sidebar-group flex flex-col gap-2">
      <h2 class="border-b pb-2 text-[13px] font-semibold tracking-wide">
        {{ $t("side.nodesPalette") }}
      </h2>
      <div class="draggable-container flex flex-col items-center gap-4 py-2">
        <div class="palette-group w-full">
          <div class="palette-title text-[11px] uppercase tracking-wide">{{ $t("side.mainNodes") }}</div>
          <div class="palette-items flex flex-col items-center gap-3 pt-2">
            <figure
              id="draggable-host"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.host')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="host" class="h-10 w-10" :src="icons.host" draggable="false" />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.host") }}</figcaption>
            </figure>
            <figure
              id="draggable-switch"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.switch')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch" class="h-10 w-10" :src="icons.switch" draggable="false" />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.switch") }}</figcaption>
            </figure>
            <figure
              id="draggable-controller-default"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.controller')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img
                alt="controller"
                class="h-10 w-10"
                :src="icons.controller"
                draggable="false"
              />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.controller") }}</figcaption>
            </figure>
            <figure
              id="draggable-nat"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.nat')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img
                alt="nat"
                class="h-10 w-10"
                :src="icons.nat"
                draggable="false"
              />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.nat") }}</figcaption>
            </figure>
            <figure
              id="draggable-router"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.router')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="router" class="h-10 w-10" :src="icons.router" draggable="false" />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.router") }}</figcaption>
            </figure>
          </div>
        </div>
        <div v-if="showSpecialSwitches" class="palette-group w-full">
          <div class="palette-title text-[11px] uppercase tracking-wide">{{ $t("side.specialSwitches") }}</div>
          <div class="palette-items flex flex-col items-center gap-3 pt-2">
            <figure
              id="draggable-switch-ovs"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.ovsSwitch')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch ovs" class="h-10 w-10" :src="icons.switchOvs" draggable="false" />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.ovsSwitch") }}</figcaption>
            </figure>
            <figure
              id="draggable-switch-user"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.userSwitch')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch user" class="h-10 w-10" :src="icons.switchUser" draggable="false" />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.userSwitch") }}</figcaption>
            </figure>
            <figure
              id="draggable-switch-ovsbridge"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.ovsBridge')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <img alt="switch ovsbridge" class="h-10 w-10" :src="icons.switchOvsBridge" draggable="false" />
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.ovsBridge") }}</figcaption>
            </figure>
          </div>
        </div>
        <div v-if="showSpecialControllers" class="palette-group w-full">
          <div class="palette-title text-[11px] uppercase tracking-wide">{{ $t("side.specialControllers") }}</div>
          <div class="palette-items flex flex-col items-center gap-3 pt-2">
            <figure
              id="draggable-controller-remote"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.remoteController')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <div class="controller-icon">
                <img
                  alt="controller remote"
                  class="h-10 w-10"
                  :src="icons.controller"
                  draggable="false"
                />
                <span class="controller-badge controller-badge--remote">{{ $t("nodes.remoteShort") }}</span>
              </div>
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.remote") }}</figcaption>
            </figure>
            <figure
              id="draggable-controller-ryu"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.ryuController')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <div class="controller-icon">
                <img
                  alt="controller ryu"
                  class="h-10 w-10"
                  :src="icons.controller"
                  draggable="false"
                />
                <span class="controller-badge">{{ $t("nodes.ryuShort") }}</span>
              </div>
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.ryu") }}</figcaption>
            </figure>
            <figure
              id="draggable-controller-nox"
              class="draggable-node flex w-14 flex-col items-center gap-2 text-center"
              draggable="true"
              @dragstart="handleDragStart"
              :data-tooltip="$t('nodes.noxController')"
              @mouseenter="handleTooltipMouseEnter($event)"
              @mousemove="handleTooltipMouseMove"
              @mouseleave="hideTooltip"
            >
              <div class="controller-icon">
                <img
                  alt="controller nox"
                  class="h-10 w-10"
                  :src="icons.controller"
                  draggable="false"
                />
                <span class="controller-badge">{{ $t("nodes.noxShort") }}</span>
              </div>
              <figcaption class="text-[11px] whitespace-nowrap">{{ $t("nodes.nox") }}</figcaption>
            </figure>
          </div>
        </div>
      </div>
    </div>


    <!-- Hotkeys Help Group
    <div class="sidebar-group hotkeys">
      <h2>Hotkeys</h2>
      <p><strong>d</strong>: {{ $t("side.shortcutDelete") }}</p>
      <p><strong>ctrl + a</strong>: Select all nodes</p>
      <p><strong>h</strong>: Toggle hosts visibility</p>
      <p><strong>c</strong>: Toggle controllers visibility</p>
    </div> -->
    </div>

  </div>

</template>

<script>
import hostImgLight from "@/assets/light-host.svg";
import switchImgLight from "@/assets/light-switch.svg";
import controllerImgLight from "@/assets/light-controller.svg";
import natImgLight from "@/assets/light-nat.svg";
import routerImgLight from "@/assets/light-router.svg";
import switchOvsImgLight from "@/assets/light-switch-ovs.svg";
import switchUserImgLight from "@/assets/light-switch-user.svg";
import switchOvsBridgeImgLight from "@/assets/light-switch-ovsbridge.svg";

import hostImgDark from "@/assets/host.svg";
import switchImgDark from "@/assets/switch.svg";
import controllerImgDark from "@/assets/controller.svg";
import natImgDark from "@/assets/nat.svg";
import routerImgDark from "@/assets/router.svg";
import switchOvsImgDark from "@/assets/switch-ovs.svg";
import switchUserImgDark from "@/assets/switch-user.svg";
import switchOvsBridgeImgDark from "@/assets/switch-ovsbridge.svg";

export default {
  props: {
    networkStarted: { type: Boolean, default: true },
    networkConnected: { type: Boolean, default: true },
    showSpecialSwitches: { type: Boolean, default: true },
    showSpecialControllers: { type: Boolean, default: true },
    addEdgeMode: { type: Boolean, default: false },
    pingallRunning: { type: Boolean, default: false },
    iperfRunning: { type: Boolean, default: false },
    theme: { type: String, default: "dark" },
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
    isLightTheme() {
      return this.theme === "light";
    },
    themeClass() {
      return this.isLightTheme ? "theme-light" : "theme-dark";
    },
    icons() {
      if (this.isLightTheme) {
        return {
          host: hostImgDark,
          switch: switchImgDark,
          controller: controllerImgDark,
          nat: natImgDark,
          router: routerImgDark,
          switchOvs: switchOvsImgDark,
          switchUser: switchUserImgDark,
          switchOvsBridge: switchOvsBridgeImgDark,
        };
      }
      return {
        host: hostImgLight,
        switch: switchImgLight,
        controller: controllerImgLight,
        nat: natImgLight,
        router: routerImgLight,
        switchOvs: switchOvsImgLight,
        switchUser: switchUserImgLight,
        switchOvsBridge: switchOvsBridgeImgLight,
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
  background: var(--theme-sidebar-bg);
  color: var(--theme-sidebar-color);
}

.side-scroll {
  scrollbar-width: thin;
  scrollbar-color: #007acc var(--theme-sidebar-bg);
}

.sidebar-divider {
  border-color: var(--theme-sidebar-border);
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

.side .button-control-network {
  background: var(--theme-sidebar-button-bg);
  color: var(--theme-sidebar-button-color);
  border: 1px solid var(--theme-sidebar-button-border);
}

.side .button-control-network:hover {
  background: var(--theme-sidebar-button-hover);
}

.side .button-control-network:active,
.side .button-control-network:focus-visible {
  background: var(--theme-sidebar-button-active-bg);
  border-color: var(--theme-sidebar-button-active-border);
  color: var(--theme-sidebar-button-active-color);
}

.sidebar-tooltip {
  position: fixed;
  pointer-events: none;
  background: var(--theme-node-context-bg);
  color: var(--theme-node-context-color);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  border: 1px solid var(--theme-node-context-border);
  white-space: nowrap;
  z-index: 30;
  transition: opacity 0.1s ease;
}

.button-control-network:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  background: var(--theme-sidebar-button-bg);
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
  color: var(--theme-sidebar-color);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  position: relative;
}

.icon-button:hover {
  background-color: var(--theme-icon-button-hover);
}

.sidebar-group h2 {
  color: var(--theme-sidebar-color) !important;
  border-bottom-color: var(--theme-sidebar-border) !important;
}

.palette-title {
  color: var(--theme-sidebar-muted) !important;
}

.side .label,
.side figcaption {
  color: var(--theme-sidebar-color) !important;
}

/* SCROLLBAR FOR WEBKIT (Chrome, Edge, Safari) */
.side-scroll::-webkit-scrollbar {
  width: 8px;
}

.side-scroll::-webkit-scrollbar-track {
  background: var(--theme-sidebar-bg);
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
  background: var(--theme-input-bg);
  color: var(--theme-sidebar-color);
  border: 1px solid var(--theme-input-border);
  border-radius: 4px;
  padding: 4px 6px;
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
