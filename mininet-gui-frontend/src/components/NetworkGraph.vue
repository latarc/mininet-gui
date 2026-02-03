<script setup>
import { Network } from "vis-network/peer";
import { DataSet } from "vis-data/peer";

import {
  getHosts,
  getSwitches,
  getControllers,
  getNats,
  getRouters,
  getEdges,
  getNodeStats,
  deployHost,
  deployNat,
  deployRouter,
  deployLink,
  deployController,
  deploySwitch,
  assocSwitch,
  updateController,
  requestStartNetwork,
  requestStopNetwork,
  requestFullResetNetwork,
  requestRunPingall,
  runIperf,
  deleteNode,
  deleteLink,
  updateNodePosition,
  requestExportNetwork,
  requestExportMininetScript,
  requestImportNetwork,
  removeAssociation,
  getAddressingPlan,
  getSnifferState,
  getHealthStatus,
  startSniffer,
  stopSniffer,
  exportSnifferPcap,
  getBackendVersion,
  getRyuApps,
} from "../core/api";
import { buildOptions } from "../core/options";
import Side from "./Side.vue";
import Modal from "./Modal.vue";
import Webshell from "./Webshell.vue";
import NodeStats from "./NodeStats.vue";
import LinkStats from "./LinkStats.vue";
import PingallResults from "./PingallResults.vue";
import ControllerForm from "./ControllerForm.vue";
import TopologyForm from "./TopologyForm.vue";
import frontendPackage from "../../package.json";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

import switchImgLight from "@/assets/light-switch.svg";
import switchOvsImgLight from "@/assets/light-switch-ovs.svg";
import switchOvsBridgeImgLight from "@/assets/light-switch-ovsbridge.svg";
import switchUserImgLight from "@/assets/light-switch-user.svg";
import hostImgLight from "@/assets/light-host.svg";
import natImgLight from "@/assets/light-nat.svg";
import routerImgLight from "@/assets/light-router.svg";

import switchImgDark from "@/assets/switch.svg";
import switchOvsImgDark from "@/assets/switch-ovs.svg";
import switchOvsBridgeImgDark from "@/assets/switch-ovsbridge.svg";
import switchUserImgDark from "@/assets/switch-user.svg";
import hostImgDark from "@/assets/host.svg";
import natImgDark from "@/assets/nat.svg";
import routerImgDark from "@/assets/router.svg";
import logoImage from "@/assets/logo-mininet-gui.png";
</script>

<template>
  <div :class="['app-shell', themeClass]">
    <div v-if="!mininetConnected" class="health-overlay">
      <div class="health-overlay__card">
        <p>{{ $t("status.backendDisconnected") }}</p>
        <button type="button" class="menu-action health-overlay__retry" @click="refreshBackendHealth">
          {{ $t("actions.retry") }}
        </button>
      </div>
    </div>
    <div ref="topbar" :class="['topbar', themeClass]">
      <div class="topbar-title">{{ $t("app.title") }}</div>
      <div class="menu-bar">
        <div class="menu-item-wrapper" @mouseenter="handleMenuHover('file')">
          <button
            type="button"
            class="menu-item"
            :class="{ open: fileMenuOpen }"
            @click.stop="toggleFileMenu"
          >
            {{ $t("menu.file") }}
          </button>
          <div v-if="fileMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleNewTopology">
              {{ $t("menu.newTopology") }}
            </button>
            <button type="button" class="menu-action" @click="handleOpenTopology">
              {{ $t("menu.openTopology") }}
            </button>
            <button type="button" class="menu-action" @click="handleSaveTopology">
              {{ $t("menu.saveTopology") }}
            </button>
            <div class="menu-separator"></div>
            <button type="button" class="menu-action" @click="handleExportScript">
              {{ $t("menu.exportScript") }}
            </button>
            <button type="button" class="menu-action" @click="handleExportSniffer">
              {{ $t("menu.exportSniffer") }}
            </button>
            <button type="button" class="menu-action" @click="handleExportPng">
              {{ $t("menu.exportPng") }}
            </button>
            <button type="button" class="menu-action" @click="handleExportAddressingPlan">
              {{ $t("menu.exportAddressing") }}
            </button>
            <div class="menu-separator"></div>
            <button type="button" class="menu-action" @click="handleOpenSettings">
              {{ $t("menu.settings") }}
            </button>
          </div>
        </div>
        <div class="menu-item-wrapper" @mouseenter="handleMenuHover('view')">
          <button
            type="button"
            class="menu-item"
            :class="{ open: viewMenuOpen }"
            @click.stop="toggleViewMenu"
          >
            {{ $t("menu.view") }}
          </button>
          <div v-if="viewMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleCollapseAllViews">
              {{ $t("menu.collapseViews") }}
            </button>
            <button type="button" class="menu-action" @click="handleExpandAllViews">
              {{ $t("menu.expandViews") }}
            </button>
            <div class="menu-separator"></div>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showHosts" @change="handleShowHostsSetting" />
              {{ $t("menu.showHosts") }}
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showControllers" @change="handleShowControllersSetting" />
              {{ $t("menu.showControllers") }}
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showSpecialSwitches" @change="persistSettings" />
              {{ $t("menu.showSpecialSwitches") }}
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showSpecialControllers" @change="persistSettings" />
              {{ $t("menu.showSpecialControllers") }}
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showHostIp" @change="persistSettings" />
              {{ $t("menu.showHostIp") }}
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showSwitchDpids" @change="persistSettings" />
              {{ $t("menu.showSwitchDpids") }}
            </label>
            <label class="menu-checkbox">
              <input type="checkbox" v-model="settings.showPortLabels" @change="persistSettings" />
              {{ $t("menu.showPortLabels") }}
            </label>
            <div class="menu-separator"></div>
            <label class="menu-checkbox">
              <input
                type="checkbox"
                v-model="settings.theme"
                :true-value="'light'"
                :false-value="'dark'"
                @change="handleThemeSetting"
              />
              {{ $t("menu.lightTheme") }}
            </label>
          </div>
        </div>
        <div class="menu-item-wrapper" @mouseenter="handleMenuHover('run')">
          <button
            type="button"
            class="menu-item"
            :class="{ open: runMenuOpen }"
            @click.stop="toggleRunMenu"
          >
            {{ $t("menu.run") }}
          </button>
          <div v-if="runMenuOpen" class="menu-dropdown" @click.stop>
            <button
              type="button"
              class="menu-action"
              @click="handleStartNetwork"
              :disabled="networkStarted || networkCommandInFlight || !mininetConnected"
            >
              {{ $t("menu.startNetwork") }}
            </button>
            <button
              type="button"
              class="menu-action"
              @click="handleStopNetwork"
              :disabled="!networkStarted || networkCommandInFlight || !mininetConnected"
            >
              {{ $t("menu.stopNetwork") }}
            </button>
            <button
              type="button"
              class="menu-action"
              @click="handleRestartNetwork"
              :disabled="networkCommandInFlight || !mininetConnected"
            >
              {{ $t("menu.restartNetwork") }}
            </button>
          </div>
        </div>
        <div class="menu-item-wrapper" @mouseenter="handleMenuHover('tools')">
          <button
            type="button"
            class="menu-item"
            :class="{ open: toolsMenuOpen }"
            @click.stop="toggleToolsMenu"
          >
            {{ $t("menu.tools") }}
          </button>
          <div v-if="toolsMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleRunIperf">
              {{ $t("menu.runIperf") }}
            </button>
            <button type="button" class="menu-action" @click="handleRunPingall">
              {{ $t("menu.runPingall") }}
            </button>
            <button type="button" class="menu-action" @click="handleGenerateTopology">
              {{ $t("menu.generateTopology") }}
            </button>
            <div class="menu-separator"></div>
            <button type="button" class="menu-action" @click="handleStartSniffer">
              {{ $t("menu.startSniffer") }}
            </button>
            <button type="button" class="menu-action" @click="handleStopSniffer">
              {{ $t("menu.stopSniffer") }}
            </button>
          </div>
        </div>
        <div class="menu-item-wrapper" @mouseenter="handleMenuHover('help')">
          <button
            type="button"
            class="menu-item"
            :class="{ open: helpMenuOpen }"
            @click.stop="toggleHelpMenu"
          >
            {{ $t("menu.help") }}
          </button>
          <div v-if="helpMenuOpen" class="menu-dropdown" @click.stop>
            <button type="button" class="menu-action" @click="handleOpenUsage">
              {{ $t("menu.usage") }}
            </button>
            <button type="button" class="menu-action" @click="handleOpenDocumentation">
              {{ $t("menu.openDocs") }}
            </button>
            <button type="button" class="menu-action" @click="handleOpenAbout">
              {{ $t("menu.about") }}
            </button>
          </div>
        </div>
      </div>
      <input
        ref="topologyFileInput"
        type="file"
        accept=".json"
        class="menu-file-input"
        @change="handleFileUpload"
      />
    </div>
    <div class="layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- Side panel (left) -->

        <div class="side-container">
        <Side
          @runPingall="showPingallModal"
          @runIperf="showIperfModal"
          @closeAllActiveModes="closeAllActiveModes"
          @toggleShowHosts="toggleShowHosts"
          @toggleShowControllers="toggleShowControllers"
          @createTopology="showTopologyFormModal"
          @toggleSidebar="handleSidebarToggle"
          @doSelectAll="doSelectAll"
          @toggleAddEdgeMode="handleToggleAddEdgeMode"
          @deleteSelected="doDeleteSelected"
          @keydown.ctrl.a.prevent="doSelectAll"
            :networkStarted="networkStarted"
            :networkConnected="mininetConnected"
            :showSpecialSwitches="settings.showSpecialSwitches"
            :showSpecialControllers="settings.showSpecialControllers"
            :addEdgeMode="addEdgeMode"
            :pingallRunning="pingallRunning"
            :iperfRunning="iperfBusy"
            :theme="settings.theme"
            :collapsed="sidebarCollapsed"
          />
        </div>
      
      <!-- Main Content (Graph + WebShell) -->
      <div class="main-content">
      <div ref="graphWrapper" class="graph-wrapper">
      <div ref="graph" id="network-graph" :class="['network-graph', themeClass]"
        @drop.prevent="handleDrop"
        @dragenter.prevent
        @dragover.prevent
        @click="hideContextMenu"
        @keydown.esc="closeAllActiveModes"
        @keydown.h="toggleShowHosts"
        @keydown.c="toggleShowControllers"
        @keydown.e="enterAddEdgeMode"
        @keydown.d="doDeleteSelected"
        @keydown.delete="doDeleteSelected"
        @keydown.ctrl.a.prevent="doSelectAll"
        ></div>
        <div
          v-show="selectionBox.active"
          class="selection-rect"
          :style="selectionRectStyle"
        ></div>
      </div>
      <div
        v-if="contextMenu.visible"
        class="node-context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <button type="button" class="node-context-item" @click="openWebshellFromMenu">
          {{ $t("context.openWebshell") }}
        </button>
        <button type="button" class="node-context-item" @click="openNodeStatsFromMenu">
          {{ $t("context.viewNodeStats") }}
        </button>
      </div>

      <!-- WebShell at the bottom -->
      <webshell
        class="webshell"
        :nodes="nodes"
        :edges="edges"
        :snifferActive="snifferActive"
        :terminalSessions="terminalSessions"
        :preferredView="webshellView"
        :focusNodeId="webshellFocusId"
        :minimized="webshellMinimized"
        :openaiKey="settings.openaiApiKey"
        :llmHandlers="llmHandlers"
        :theme="settings.theme"
        @viewChange="handleWebshellViewChange"
        @toggleSniffer="toggleSniffer"
        @minimizeChange="handleWebshellMinimizeChange"
        @closeSession="handleCloseSession"
      />
      </div>
    </div>
    <div :class="['status-bar', themeClass]">
      <div class="status-bar__right">
        <span
          class="status-dot"
          :class="mininetConnected ? 'status-dot--started' : 'status-dot--stopped'"
        ></span>
        <div class="status-bar__text">
          <span class="status-bar__primary">
            {{ mininetConnected ? $t("status.connected") : $t("status.disconnected") }}
          </span>
          <span class="status-bar__version">
            {{ $t("status.mininetVersion", { version: mininetVersion || $t("status.unknown") }) }}
          </span>
          <span class="status-bar__network">
            <span class="network-state-dot" :class="networkStateIndicator"></span>
            {{ $t("status.networkState", { state: networkStarted ? $t("status.started") : $t("status.stopped") }) }}
          </span>
          <span class="status-bar__counts">
            {{ $t("status.counts", { hosts: networkCounts.hosts, controllers: networkCounts.controllers, switches: networkCounts.switches }) }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <modal
      :show="showModal"
      :theme="settings.theme"
      @close="closeModal"
      @keydown.esc="closeModal"
    >
      <template #header>
        <h3>{{ modalHeader }}</h3>
      </template>
      <template #body>
        <node-stats
          v-if="modalOption === 'nodeStats'"
          :stats="modalData"
          @hostUpdated="handleHostUpdated"
          @editController="showControllerEditModal"
        />
        <link-stats v-if="modalOption === 'linkStats'" :link="modalData" @linkUpdated="handleLinkUpdated" />
        <pingall-results v-if="modalOption === 'pingall'" :pingResults="modalData" />
        <div v-if="modalOption === 'iperf'" class="modal-ui">
          <div class="modal-tabs">
            <button type="button" class="modal-tab" :class="{ 'is-active': iperfTab === 'config' }" @click="iperfTab = 'config'">
              {{ $t("iperf.configTab") }}
            </button>
            <button type="button" class="modal-tab" :class="{ 'is-active': iperfTab === 'results' }" @click="iperfTab = 'results'">
              {{ $t("iperf.resultsTab") }}
            </button>
          </div>
          <div class="modal-tab-panels">
            <div class="modal-section tab-panel" :class="{ 'is-hidden': iperfTab !== 'config' }">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("iperf.configTitle") }}</div>
              <span class="modal-muted">{{ $t("iperf.configHint") }}</span>
            </div>
            <div class="modal-form-grid">
              <label class="modal-field" for="iperf-client">
                {{ $t("iperf.client") }}
                <select id="iperf-client" v-model="iperfForm.client" class="modal-select">
                  <option value="" disabled>{{ $t("iperf.selectClient") }}</option>
                  <option v-for="host in Object.values(hosts)" :key="host.id" :value="host.id">
                    {{ host.id }}
                  </option>
                </select>
              </label>
              <label class="modal-field" for="iperf-server">
                {{ $t("iperf.server") }}
                <select id="iperf-server" v-model="iperfForm.server" class="modal-select">
                  <option value="" disabled>{{ $t("iperf.selectServer") }}</option>
                  <option v-for="host in Object.values(hosts)" :key="host.id" :value="host.id">
                    {{ host.id }}
                  </option>
                </select>
              </label>
              <label class="modal-field" for="iperf-proto">
                {{ $t("iperf.protocol") }}
                <select id="iperf-proto" v-model="iperfForm.l4_type" class="modal-select">
                  <option value="TCP">TCP</option>
                  <option value="UDP">UDP</option>
                </select>
              </label>
              <label class="modal-field" for="iperf-duration">
                {{ $t("iperf.duration") }}
                <input
                  id="iperf-duration"
                  v-model.number="iperfForm.seconds"
                  class="modal-input"
                  type="number"
                  min="1"
                />
              </label>
              <label class="modal-field" for="iperf-udp-bw">
                {{ $t("iperf.udpBw") }}
                <input
                  id="iperf-udp-bw"
                  v-model="iperfForm.udp_bw"
                  class="modal-input"
                  type="text"
                  :disabled="iperfForm.l4_type !== 'UDP'"
                  placeholder="10M"
                />
              </label>
              <label class="modal-field" for="iperf-format">
                {{ $t("iperf.format") }}
                <input
                  id="iperf-format"
                  v-model="iperfForm.fmt"
                  class="modal-input"
                  type="text"
                  placeholder="M"
                />
              </label>
              <label class="modal-field" for="iperf-port">
                {{ $t("iperf.port") }}
                <input
                  id="iperf-port"
                  v-model.number="iperfForm.port"
                  class="modal-input"
                  type="number"
                  min="1"
                  max="65535"
                />
              </label>
            </div>
            <div class="modal-actions">
              <button
                class="modal-button modal-button--primary"
                type="button"
                :disabled="iperfBusy || !iperfForm.client || !iperfForm.server || iperfForm.client === iperfForm.server"
                @click="runIperfTest"
              >
                {{ iperfBusy ? $t("iperf.running") : $t("menu.runIperf") }}
              </button>
              <span v-if="iperfError" class="modal-error">{{ iperfError }}</span>
            </div>
            </div>
            <div class="modal-section tab-panel" :class="{ 'is-hidden': iperfTab !== 'results' }">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("iperf.result") }}</div>
              <span class="modal-muted">{{ iperfResult ? $t("iperf.resultReady") : $t("iperf.noResult") }}</span>
            </div>
            <pre class="modal-pre">{{ iperfResult ? formatIperfResult(iperfResult) : $t("iperf.noResultBody") }}</pre>
            </div>
          </div>
        </div>
        <controller-form
          v-if="modalOption === 'controllerForm'"
          :preset-type="controllerFormPreset"
          :ryu-apps="ryuApps"
          :controller="controllerFormData"
          @form-submit="handleControllerFormSubmit"
          @form-update="handleControllerFormUpdate"
        />
        <topology-form v-if="modalOption === 'topologyForm'" :controllers="controllers" @form-submit="handleTopologyFormSubmit" />
        <div v-if="modalOption === 'usage'" class="modal-ui">
          <div class="modal-tabs">
            <button type="button" class="modal-tab" :class="{ 'is-active': helpTab === 'welcome' }" @click="helpTab = 'welcome'">{{ $t("help.welcomeTab") }}</button>
            <button type="button" class="modal-tab" :class="{ 'is-active': helpTab === 'shortcuts' }" @click="helpTab = 'shortcuts'">{{ $t("help.shortcutsTab") }}</button>
            <button type="button" class="modal-tab" :class="{ 'is-active': helpTab === 'devices' }" @click="helpTab = 'devices'">{{ $t("help.devicesTab") }}</button>
          </div>
          <div class="modal-section">
            <div class="modal-tab-panels">
              <div class="modal-stack tab-panel" :class="{ 'is-hidden': helpTab !== 'welcome' }">
                <p>{{ $t("help.welcomeLine1") }}</p>
                <p>{{ $t("help.welcomeLine2") }}</p>
                <p>{{ $t("help.welcomeLine3") }}</p>
                <p>{{ $t("help.welcomeLine4") }}</p>
              </div>
              <div class="modal-stack tab-panel" :class="{ 'is-hidden': helpTab !== 'shortcuts' }">
                <p>{{ $t("help.shortcuts1") }}</p>
                <p>{{ $t("help.shortcuts2") }}</p>
                <p>{{ $t("help.shortcuts3") }}</p>
                <p>{{ $t("help.shortcuts4") }}</p>
                <p>{{ $t("help.shortcuts5") }}</p>
                <p>{{ $t("help.shortcuts6") }}</p>
              </div>
              <div class="modal-stack tab-panel" :class="{ 'is-hidden': helpTab !== 'devices' }">
                <p>{{ $t("help.deviceHost") }}</p>
                <p>{{ $t("help.deviceSwitch") }}</p>
                <p>{{ $t("help.deviceController") }}</p>
                <p>{{ $t("help.deviceRouter") }}</p>
                <p>{{ $t("help.deviceNat") }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-if="modalOption === 'about'" class="modal-ui">
          <div class="modal-section">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("about.title") }}</div>
            </div>
            <div class="about-grid">
              <img :src="logoImage" alt="Mininet GUI logo" class="about-logo" />
              <div class="about-details">
                <p>{{ $t("about.frontendVersion", { version: frontendVersion }) }}</p>
                <p>{{ $t("about.backendVersion", { version: backendVersion }) }}</p>
                <p>{{ $t("about.mininetVersion", { version: mininetVersion }) }}</p>
                <p>{{ $t("about.authors") }}</p>
                <p>
                  {{ $t("about.repository") }}
                  <a
                    class="about-link"
                    href="https://github.com/latarc/mininet-gui"
                    target="_blank"
                    rel="noreferrer"
                  >
                    https://github.com/latarc/mininet-gui
                  </a>
                </p>
                <p>{{ $t("about.license") }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-if="modalOption === 'settings'" class="modal-ui">
          <div class="modal-section">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("settings.viewTitle") }}</div>
            </div>
            <div class="modal-form-grid">
              <label class="modal-field">
                {{ $t("settings.language") }}
                <select v-model="settings.language" class="modal-select" @change="handleLanguageChange">
                  <option value="en">{{ $t("language.english") }}</option>
                  <option value="pt">{{ $t("language.portuguese") }}</option>
                </select>
              </label>
            </div>
            <div class="settings-grid">
              <label class="settings-toggle">
                <input
                  type="checkbox"
                  v-model="settings.theme"
                  :true-value="'light'"
                  :false-value="'dark'"
                  @change="handleThemeSetting"
                />
                <span>{{ $t("settings.lightTheme") }}</span>
              </label>
              <label class="settings-toggle">
                <input type="checkbox" v-model="settings.showHosts" @change="handleShowHostsSetting" />
                <span>{{ $t("menu.showHosts") }}</span>
              </label>
              <label class="settings-toggle">
                <input type="checkbox" v-model="settings.showControllers" @change="handleShowControllersSetting" />
                <span>{{ $t("menu.showControllers") }}</span>
              </label>
              <label class="settings-toggle">
                <input type="checkbox" v-model="settings.showSpecialSwitches" @change="persistSettings" />
                <span>{{ $t("menu.showSpecialSwitches") }}</span>
              </label>
              <label class="settings-toggle">
                <input type="checkbox" v-model="settings.showSpecialControllers" @change="persistSettings" />
                <span>{{ $t("menu.showSpecialControllers") }}</span>
              </label>
              <label class="settings-toggle">
                <input type="checkbox" v-model="settings.showHostIp" @change="persistSettings" />
                <span>{{ $t("menu.showHostIp") }}</span>
              </label>
              <label class="settings-toggle">
                <input type="checkbox" v-model="settings.showSwitchDpids" @change="persistSettings" />
                <span>{{ $t("menu.showSwitchDpids") }}</span>
              </label>
            </div>
          </div>
          <div class="modal-section">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("settings.defaultsTitle") }}</div>
            </div>
            <div class="modal-form-grid">
              <label class="modal-field">
                {{ $t("settings.defaultOpenflow") }}
                <select v-model="settings.switchOpenflow" class="modal-select" @change="persistSettings">
                  <option value="">{{ $t("node.openflowAuto") }}</option>
                  <option value="OpenFlow10">OpenFlow10</option>
                  <option value="OpenFlow11">OpenFlow11</option>
                  <option value="OpenFlow12">OpenFlow12</option>
                  <option value="OpenFlow13">OpenFlow13</option>
                  <option value="OpenFlow14">OpenFlow14</option>
                  <option value="OpenFlow15">OpenFlow15</option>
                </select>
              </label>
            </div>
            <div class="modal-divider"></div>
            <div class="modal-section__title">{{ $t("settings.defaultLinkAttributes") }}</div>
            <div class="modal-form-grid">
              <label class="modal-field">
                {{ $t("link.bandwidth") }}
                <input type="number" v-model="settings.linkOptions.bw" class="modal-input" @change="persistSettings" min="0" />
              </label>
              <label class="modal-field">
                {{ $t("link.delay") }}
                <input type="number" v-model="settings.linkOptions.delay" class="modal-input" @change="persistSettings" min="0" />
              </label>
              <label class="modal-field">
                {{ $t("link.jitter") }}
                <input type="number" v-model="settings.linkOptions.jitter" class="modal-input" @change="persistSettings" min="0" />
              </label>
              <label class="modal-field">
                {{ $t("link.loss") }}
                <input type="number" v-model="settings.linkOptions.loss" class="modal-input" @change="persistSettings" min="0" max="100" />
              </label>
              <label class="modal-field">
                {{ $t("link.maxQueue") }}
                <input type="number" v-model="settings.linkOptions.max_queue_size" class="modal-input" @change="persistSettings" min="0" />
              </label>
              <label class="modal-field settings-toggle">
                <input type="checkbox" v-model="settings.linkOptions.use_htb" @change="persistSettings" />
                <span>{{ $t("link.useHtb") }}</span>
              </label>
            </div>
          </div>
          <div class="modal-section">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("settings.integrationsTitle") }}</div>
            </div>
            <div class="modal-form-grid">
              <label class="modal-field">
                {{ $t("settings.openaiKey") }}
                <input
                  type="password"
                  v-model="settings.openaiApiKey"
                  class="modal-input"
                  @change="persistSettings"
                  placeholder="sk-..."
                />
              </label>
            </div>
          </div>
        </div>
        <div v-if="modalOption === 'confirmReset'" class="modal-ui">
          <div class="modal-section">
            <div class="modal-section__header">
              <div class="modal-section__title">{{ $t("confirm.resetTopologyTitle") }}</div>
            </div>
            <p class="modal-muted">{{ $t("confirm.resetTopologyText") }}</p>
            <div class="modal-actions">
              <button class="modal-button" @click="closeModal">
                {{ $t("actions.cancel") }}
              </button>
              <button class="modal-button modal-button--danger" @click="confirmResetTopology">
                {{ $t("actions.resetTopology") }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </modal>
  </Teleport>
</template>

<script>
export default {
  name: "NetworkGraph",
  components: {
    Side,
    NodeStats,
    LinkStats,
    PingallResults,
    ControllerForm,
    TopologyForm,
  },
  data() {
    return {
      hosts: {},
      switches: {},
      controllers: {},
      nats: {},
      routers: {},
      links: [],
      nodes: new DataSet(),
      edges: new DataSet(),
      addEdgeMode: false,
      networkStarted: false,
      networkCommandInFlight: false,
      runMenuOpen: false,
      toolsMenuOpen: false,
      viewMenuOpen: false,
      mininetConnected: true,
      healthTimer: null,
      pingallRunning: false,
      iperfBusy: false,
      iperfError: "",
      iperfResult: null,
      iperfTab: "config",
      iperfForm: {
        client: "",
        server: "",
        l4_type: "TCP",
        seconds: 5,
        udp_bw: "",
        fmt: "",
        port: "",
      },
      snifferActive: false,
      hostsHidden: false,
      controllersHidden: false,
      sidebarCollapsed: false,
      webshellMinimized: false,
      showModal: false,
      modalHeader: "",
      modalOption: null,
      modalData: {},
      linkModalEdgeId: null,
      helpTab: "welcome",
      controllerFormPreset: null,
      controllerFormData: null,
      ryuApps: [],
      webshellView: null,
      webshellFocusId: null,
      webshellActiveView: null,
      terminalSessions: [],
      terminalSessionCounters: {},
      contextMenu: {
        visible: false,
        x: 0,
        y: 0,
        nodeId: null,
      },
      fileMenuOpen: false,
      helpMenuOpen: false,
      boundHandleGlobalClick: null,
      frontendVersion: frontendPackage?.version || "unknown",
      backendVersion: "unknown",
      mininetVersion: "unknown",
      selectionBox: {
        active: false,
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        append: false,
      },
      boundSelectionMouseDown: null,
      boundSelectionMouseMove: null,
      boundSelectionMouseUp: null,
      panState: {
        active: false,
        moved: false,
        startX: 0,
        startY: 0,
        startViewX: 0,
        startViewY: 0,
        scale: 1,
      },
      boundPanMouseDown: null,
      boundPanMouseMove: null,
      boundPanMouseUp: null,
      boundContextMenu: null,
      settings: {
        showHosts: true,
        showControllers: true,
        showSpecialSwitches: true,
        showSpecialControllers: true,
        showHostIp: false,
        showSwitchDpids: false,
        showPortLabels: false,
        theme: "dark",
        language: "en",
        switchOpenflow: "",
        openaiApiKey: "",
        linkOptions: {
          bw: "",
          delay: "",
          jitter: "",
          loss: "",
          max_queue_size: "",
          use_htb: false,
        },
      },
    };
  },
  computed: {
    isLightTheme() {
      return this.settings.theme === "light";
    },
    themeClass() {
      return this.isLightTheme ? "theme-light" : "theme-dark";
    },
    network() {
      const computedNetwork = this.computeNetwork();
      console.log("[NetworkGraph] computed:", computedNetwork);
      return computedNetwork;
    },
    networkCounts() {
      return {
        hosts: Object.keys(this.hosts || {}).length,
        controllers: Object.keys(this.controllers || {}).length,
        switches: Object.keys(this.switches || {}).length,
      };
    },
    networkStateIndicator() {
      if (this.networkCommandInFlight) return "network-state--pending";
      return this.networkStarted ? "network-state--started" : "network-state--stopped";
    },
    llmHandlers() {
      return {
        createHost: this.llmCreateHost,
        createSwitch: this.llmCreateSwitch,
        createController: this.llmCreateController,
        createLink: this.llmCreateLink,
        associateSwitch: this.llmAssociateSwitch,
        getTopology: this.llmGetTopology,
        runCommand: this.llmRunCommand,
        deleteNode: this.llmDeleteNode,
      };
    },
    selectionRectStyle() {
      const left = Math.min(this.selectionBox.startX, this.selectionBox.endX);
      const top = Math.min(this.selectionBox.startY, this.selectionBox.endY);
      const width = Math.abs(this.selectionBox.endX - this.selectionBox.startX);
      const height = Math.abs(this.selectionBox.endY - this.selectionBox.startY);
      return {
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        height: `${height}px`,
      };
    },
  },
  async mounted() {
    this.loadSettings();
    this.maybeShowFirstRunHelp();
    await this.syncSnifferState();
    this.snifferStateTimer = setInterval(() => this.syncSnifferState(), 5000);
    await this.loadRyuApps();
    this.setupNetwork();
    this.bindSelectionEvents();
    this.bindTopbarEvents();
    this.loadVersions();
    await this.refreshBackendHealth();
    this.healthTimer = setInterval(() => this.refreshBackendHealth(), 2000);
  },
  beforeUnmount() {
    if (this.snifferStateTimer) clearInterval(this.snifferStateTimer);
    this.unbindSelectionEvents();
    this.unbindTopbarEvents();
    if (this.healthTimer) clearInterval(this.healthTimer);
  },
  methods: {
    currentAssets() {
      if (this.isLightTheme) {
        return {
          host: hostImgDark,
          nat: natImgDark,
          router: routerImgDark,
          switch: switchImgDark,
          switchOvs: switchOvsImgDark,
          switchOvsBridge: switchOvsBridgeImgDark,
          switchUser: switchUserImgDark,
        };
      }
      return {
        host: hostImgLight,
        nat: natImgLight,
        router: routerImgLight,
        switch: switchImgLight,
        switchOvs: switchOvsImgLight,
        switchOvsBridge: switchOvsBridgeImgLight,
        switchUser: switchUserImgLight,
      };
    },
    nodeBaseColor() {
      const highlight = this.isLightTheme ? "#bdbdbd" : "#848484";
      const background = this.isLightTheme ? "#f3f3f3" : "#252526";
      return {
        background,
        border: "#00000000",
        highlight: { background: highlight, border: highlight },
      };
    },
    portLabelFontColor() {
      return this.isLightTheme ? "#2b2b2b" : "#e6e6e6";
    },
    linkInactiveColor() {
      return this.isLightTheme ? "#7a7a7aff" : "#999999ff";
    },
    controllerLinkColor() {
      return this.isLightTheme ? "#8a8a8a" : "#777788af";
    },
    applyThemeSetting() {
      const toggleClass = (el, className, enabled) => {
        if (!el) return;
        if (enabled) el.classList.add(className);
        else el.classList.remove(className);
      };
      const root = document.documentElement;
      const body = document.body;
      const app = document.getElementById("app");
      const targetSet = [root, body, app];
      targetSet.forEach((el) => toggleClass(el, "theme-light", this.isLightTheme));
      targetSet.forEach((el) => toggleClass(el, "theme-dark", !this.isLightTheme));
    },
    handleThemeSetting() {
      this.applyThemeSetting();
      this.applyNetworkTheme();
      this.persistSettings();
    },
    applyNetworkTheme() {
      if (this.network) {
        this.network.setOptions(buildOptions(this.settings.theme));
      }
      const assets = this.currentAssets();
      if (this.nodes?.forEach) {
        this.nodes.forEach((node) => {
          if (node.type === "controller") {
            this.nodes.updateOnly({
              id: node.id,
              color: this.nodeBaseColor(),
              image: this.controllerImageForColor(this.controllerIconColor(node)),
            });
            return;
          }
          if (node.type === "host") {
            this.nodes.updateOnly({ id: node.id, color: this.nodeBaseColor(), image: assets.host });
            return;
          }
          if (node.type === "switch" || node.type === "sw") {
            this.nodes.updateOnly({
              id: node.id,
              color: this.nodeBaseColor(),
              image: this.switchImageForType(node.switch_type),
            });
            return;
          }
          if (node.type === "nat") {
            this.nodes.updateOnly({ id: node.id, color: this.nodeBaseColor(), image: assets.nat });
            return;
          }
          if (node.type === "router") {
            this.nodes.updateOnly({ id: node.id, color: this.nodeBaseColor(), image: assets.router });
          }
        });
      }
      if (this.edges?.forEach) {
        const updates = [];
        this.edges.forEach((edge) => {
          if (!edge?.dashes?.length) return;
          const currentColor = edge.color;
          const normalizedColor =
            typeof currentColor === "object" && currentColor !== null && "color" in currentColor
              ? { ...currentColor, color: this.controllerLinkColor() }
              : { color: this.controllerLinkColor() };
          updates.push({ id: edge.id, color: normalizedColor });
        });
        if (updates.length) this.edges.update(updates);
      }
      this.updateLinkColors();
    },
    switchImageForType(type) {
      const assets = this.currentAssets();
      const key = (type || "ovskernel").toLowerCase();
      if (key === "user") return assets.switchUser;
      if (key === "ovs") return assets.switchOvs;
      if (key === "ovsbridge") return assets.switchOvsBridge;
      if (key === "ovskernel") return assets.switch;
      return assets.switch;
    },
    async loadVersions() {
      const backendInfo = await getBackendVersion();
      if (!backendInfo) return;
      if (backendInfo.version) this.backendVersion = backendInfo.version;
      if (backendInfo.mininet_version) this.mininetVersion = backendInfo.mininet_version;
    },
    async loadRyuApps() {
      this.ryuApps = await getRyuApps();
    },
    bindTopbarEvents() {
      if (!this.boundHandleGlobalClick) {
        this.boundHandleGlobalClick = this.handleGlobalClick.bind(this);
      }
      document.addEventListener("click", this.boundHandleGlobalClick);
    },
    unbindTopbarEvents() {
      if (this.boundHandleGlobalClick) {
        document.removeEventListener("click", this.boundHandleGlobalClick);
      }
    },
    handleGlobalClick(event) {
      const topbar = this.$refs.topbar;
      if (!topbar) return;
      if (this.fileMenuOpen && !topbar.contains(event.target)) {
        this.fileMenuOpen = false;
      }
      if (this.helpMenuOpen && !topbar.contains(event.target)) {
        this.helpMenuOpen = false;
      }
      if (this.runMenuOpen && !topbar.contains(event.target)) {
        this.runMenuOpen = false;
      }
      if (this.toolsMenuOpen && !topbar.contains(event.target)) {
        this.toolsMenuOpen = false;
      }
      if (this.viewMenuOpen && !topbar.contains(event.target)) {
        this.viewMenuOpen = false;
      }
    },
    isAnyMenuOpen() {
      return (
        this.fileMenuOpen ||
        this.helpMenuOpen ||
        this.runMenuOpen ||
        this.toolsMenuOpen ||
        this.viewMenuOpen
      );
    },
    openMenuByKey(menuKey) {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      if (menuKey === "file") this.fileMenuOpen = true;
      if (menuKey === "help") this.helpMenuOpen = true;
      if (menuKey === "run") this.runMenuOpen = true;
      if (menuKey === "tools") this.toolsMenuOpen = true;
      if (menuKey === "view") this.viewMenuOpen = true;
    },
    handleMenuHover(menuKey) {
      if (!this.isAnyMenuOpen()) return;
      if (menuKey === "file" && this.fileMenuOpen) return;
      if (menuKey === "help" && this.helpMenuOpen) return;
      if (menuKey === "run" && this.runMenuOpen) return;
      if (menuKey === "tools" && this.toolsMenuOpen) return;
      if (menuKey === "view" && this.viewMenuOpen) return;
      this.openMenuByKey(menuKey);
    },
    toggleFileMenu() {
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      this.fileMenuOpen = !this.fileMenuOpen;
    },
    toggleHelpMenu() {
      this.fileMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      this.helpMenuOpen = !this.helpMenuOpen;
    },
    toggleToolsMenu() {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.viewMenuOpen = false;
      this.toolsMenuOpen = !this.toolsMenuOpen;
    },
    toggleViewMenu() {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.runMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = !this.viewMenuOpen;
    },
    closeFileMenu() {
      this.fileMenuOpen = false;
    },
    closeHelpMenu() {
      this.helpMenuOpen = false;
    },
    closeToolsMenu() {
      this.toolsMenuOpen = false;
    },
    closeViewMenu() {
      this.viewMenuOpen = false;
    },
    toggleRunMenu() {
      this.fileMenuOpen = false;
      this.helpMenuOpen = false;
      this.toolsMenuOpen = false;
      this.viewMenuOpen = false;
      this.runMenuOpen = !this.runMenuOpen;
    },
    closeRunMenu() {
      this.runMenuOpen = false;
    },
    async handleStartNetwork() {
      this.closeRunMenu();
      if (this.networkCommandInFlight || this.networkStarted) return;
      this.networkCommandInFlight = true;
      try {
        const started = await requestStartNetwork();
        if (started) {
          this.networkStarted = true;
        }
      } finally {
        this.networkCommandInFlight = false;
        await this.refreshBackendHealth();
      }
    },
    async handleStopNetwork() {
      this.closeRunMenu();
      if (this.networkCommandInFlight || !this.networkStarted) return;
      this.networkCommandInFlight = true;
      try {
        const stopped = await requestStopNetwork();
        if (stopped) {
          this.snifferActive = false;
          this.networkStarted = false;
          await this.setupNetwork();
        }
      } finally {
        this.networkCommandInFlight = false;
        await this.refreshBackendHealth();
      }
    },
    async handleRestartNetwork() {
      this.closeRunMenu();
      if (this.networkCommandInFlight) return;
      this.networkCommandInFlight = true;
      try {
        const stopped = await requestStopNetwork();
        if (stopped) {
          this.snifferActive = false;
          this.networkStarted = false;
        }
        const restarted = await requestStartNetwork();
        if (restarted) {
          this.networkStarted = true;
          await this.setupNetwork();
        }
      } finally {
        this.networkCommandInFlight = false;
        await this.refreshBackendHealth();
      }
    },
    handleNewTopology() {
      this.closeFileMenu();
      this.showResetConfirmModal();
    },
    handleOpenTopology() {
      this.closeFileMenu();
      this.openFileDialog();
    },
    handleSaveTopology() {
      this.closeFileMenu();
      this.saveTopologyAs();
    },
    handleExportScript() {
      this.closeFileMenu();
      this.exportMininetScript();
    },
    handleExportSniffer() {
      this.closeFileMenu();
      this.exportSniffer();
    },
    handleExportPng() {
      this.closeFileMenu();
      this.exportTopologyAsPng();
    },
    handleExportAddressingPlan() {
      this.closeFileMenu();
      this.exportAddressingPlan();
    },
    handleOpenSettings() {
      this.closeFileMenu();
      this.showSettingsModal();
    },
    handleRunIperf() {
      this.closeToolsMenu();
      this.showIperfModal();
    },
    handleRunPingall() {
      this.closeToolsMenu();
      this.showPingallModal();
    },
    handleGenerateTopology() {
      this.closeToolsMenu();
      this.showTopologyFormModal();
    },
    async handleStartSniffer() {
      this.closeToolsMenu();
      if (this.snifferActive) return;
      await this.toggleSniffer();
    },
    async handleStopSniffer() {
      this.closeToolsMenu();
      if (!this.snifferActive) return;
      await this.toggleSniffer();
    },
    handleCollapseAllViews() {
      this.closeViewMenu();
      this.sidebarCollapsed = true;
      this.webshellMinimized = true;
    },
    handleExpandAllViews() {
      this.closeViewMenu();
      this.sidebarCollapsed = false;
      this.webshellMinimized = false;
    },
    handleOpenUsage() {
      this.closeHelpMenu();
      this.modalHeader = this.$t("menu.usage");
      this.modalOption = "usage";
      this.modalData = null;
      this.helpTab = "welcome";
      this.showModal = true;
    },
    handleOpenDocumentation() {
      this.closeHelpMenu();
      window.open("https://github.com/latarc/mininet-gui", "_blank", "noopener,noreferrer");
    },
    handleOpenAbout() {
      this.closeHelpMenu();
      this.modalHeader = this.$t("menu.about");
      this.modalOption = "about";
      this.modalData = null;
      this.showModal = true;
    },
    openFileDialog() {
      this.$refs.topologyFileInput?.click();
    },
    handleFileUpload(event) {
      const file = event.target.files?.[0];
      if (file) {
        this.importTopology(file);
      }
      if (event.target) event.target.value = "";
    },
    bindSelectionEvents() {
      const graphEl = this.$refs.graphWrapper;
      if (!graphEl) return;
      if (!this.boundSelectionMouseDown) {
        this.boundSelectionMouseDown = this.handleSelectionMouseDown.bind(this);
        this.boundSelectionMouseMove = this.handleSelectionMouseMove.bind(this);
        this.boundSelectionMouseUp = this.handleSelectionMouseUp.bind(this);
      }
      graphEl.addEventListener("mousedown", this.boundSelectionMouseDown);
      if (!this.boundPanMouseDown) {
        this.boundPanMouseDown = this.handlePanMouseDown.bind(this);
        this.boundPanMouseMove = this.handlePanMouseMove.bind(this);
        this.boundPanMouseUp = this.handlePanMouseUp.bind(this);
        this.boundContextMenu = this.handleContextMenu.bind(this);
      }
      graphEl.addEventListener("mousedown", this.boundPanMouseDown);
      graphEl.addEventListener("contextmenu", this.boundContextMenu);
    },
    unbindSelectionEvents() {
      const graphEl = this.$refs.graphWrapper;
      if (graphEl) {
        graphEl.removeEventListener("mousedown", this.boundSelectionMouseDown);
        graphEl.removeEventListener("mousedown", this.boundPanMouseDown);
        graphEl.removeEventListener("contextmenu", this.boundContextMenu);
      }
      window.removeEventListener("mousemove", this.boundSelectionMouseMove);
      window.removeEventListener("mouseup", this.boundSelectionMouseUp);
      window.removeEventListener("mousemove", this.boundPanMouseMove);
      window.removeEventListener("mouseup", this.boundPanMouseUp);
    },
    handleSelectionMouseDown(event) {
      if (event.button !== 0) return;
      if (this.addEdgeMode) return;
      if (!this.network || !this.$refs.graphWrapper) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const localX = event.clientX - rect.left;
      const localY = event.clientY - rect.top;
      const hitNode = this.network.getNodeAt({ x: localX, y: localY });
      if (hitNode) return;
      event.preventDefault();
      this.hideContextMenu();
      this.selectionBox = {
        active: true,
        startX: localX,
        startY: localY,
        endX: localX,
        endY: localY,
        append: event.ctrlKey || event.metaKey,
      };
      window.addEventListener("mousemove", this.boundSelectionMouseMove);
      window.addEventListener("mouseup", this.boundSelectionMouseUp);
    },
    handlePanMouseDown(event) {
      if (event.button !== 1 && event.button !== 2) return;
      if (!this.network || !this.$refs.graphWrapper) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      this.panState = {
        active: true,
        moved: false,
        startX: event.clientX - rect.left,
        startY: event.clientY - rect.top,
        startViewX: this.network.getViewPosition().x,
        startViewY: this.network.getViewPosition().y,
        scale: this.network.getScale(),
      };
      window.addEventListener("mousemove", this.boundPanMouseMove);
      window.addEventListener("mouseup", this.boundPanMouseUp);
    },
    handlePanMouseMove(event) {
      if (!this.panState.active || !this.$refs.graphWrapper || !this.network) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const currentX = event.clientX - rect.left;
      const currentY = event.clientY - rect.top;
      const dx = currentX - this.panState.startX;
      const dy = currentY - this.panState.startY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
        this.panState.moved = true;
      }
      if (this.panState.moved) {
        event.preventDefault();
        const scale = this.panState.scale || this.network.getScale();
        this.network.moveTo({
          position: {
            x: this.panState.startViewX - dx / scale,
            y: this.panState.startViewY - dy / scale,
          },
          scale,
          animation: false,
        });
      }
    },
    handlePanMouseUp() {
      if (!this.panState.active) return;
      window.removeEventListener("mousemove", this.boundPanMouseMove);
      window.removeEventListener("mouseup", this.boundPanMouseUp);
      this.panState.active = false;
    },
    handleContextMenu(event) {
      if (this.panState.moved) {
        event.preventDefault();
        this.hideContextMenu();
      }
    },
    handleSelectionMouseMove(event) {
      if (!this.selectionBox.active || !this.$refs.graphWrapper) return;
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const localX = event.clientX - rect.left;
      const localY = event.clientY - rect.top;
      this.selectionBox.endX = localX;
      this.selectionBox.endY = localY;
    },
    handleSelectionMouseUp(event) {
      if (!this.selectionBox.active) return;
      window.removeEventListener("mousemove", this.boundSelectionMouseMove);
      window.removeEventListener("mouseup", this.boundSelectionMouseUp);
      if (!this.$refs.graphWrapper || !this.network) {
        this.selectionBox.active = false;
        return;
      }
      const rect = this.$refs.graphWrapper.getBoundingClientRect();
      const localX = event.clientX - rect.left;
      const localY = event.clientY - rect.top;
      this.selectionBox.endX = localX;
      this.selectionBox.endY = localY;
      this.finalizeSelection();
    },
    finalizeSelection() {
      const left = Math.min(this.selectionBox.startX, this.selectionBox.endX);
      const top = Math.min(this.selectionBox.startY, this.selectionBox.endY);
      const width = Math.abs(this.selectionBox.endX - this.selectionBox.startX);
      const height = Math.abs(this.selectionBox.endY - this.selectionBox.startY);
      const minDrag = 4;
      if (width < minDrag && height < minDrag) {
        this.selectionBox.active = false;
        return;
      }
      const topLeft = this.network.DOMtoCanvas({ x: left, y: top });
      const bottomRight = this.network.DOMtoCanvas({ x: left + width, y: top + height });
      const rectCanvas = {
        left: Math.min(topLeft.x, bottomRight.x),
        right: Math.max(topLeft.x, bottomRight.x),
        top: Math.min(topLeft.y, bottomRight.y),
        bottom: Math.max(topLeft.y, bottomRight.y),
      };
      const positions = this.network.getPositions();
      const selected = Object.entries(positions).reduce((acc, [nodeId, canvasPos]) => {
        if (!canvasPos) return acc;
        const { x, y } = canvasPos;
        if (x < rectCanvas.left || x > rectCanvas.right) return acc;
        if (y < rectCanvas.top || y > rectCanvas.bottom) return acc;
        const nodeData = this.nodes?.get?.(nodeId);
        if (nodeData) acc.push(nodeId);
        return acc;
      }, []);
      if (this.selectionBox.append) {
        const current = this.network.getSelectedNodes();
        const merged = new Set([...current, ...selected]);
        this.network.selectNodes([...merged], true);
      } else if (selected.length) {
        this.network.selectNodes(selected, true);
      } else {
        this.network.unselectAll();
      }
      this.selectionBox.active = false;
    },
    loadSettings() {
      try {
        const raw = localStorage.getItem("mininetGuiSettings");
        if (raw) {
          const parsed = JSON.parse(raw);
          this.settings = { ...this.settings, ...parsed };
        }
      } catch (error) {
        console.warn("Failed to load settings", error);
      }
      this.applyThemeSetting();
      this.applyLocaleSetting();
      this.applyVisibilitySettings();
      this.applyPortLabels();
      this.applyNetworkTheme();
    },
    persistSettings() {
      try {
        localStorage.setItem("mininetGuiSettings", JSON.stringify(this.settings));
      } catch (error) {
        console.warn("Failed to persist settings", error);
      }
      this.applyVisibilitySettings();
      this.applyHostLabels();
      this.applySwitchLabels();
      this.applyPortLabels();
    },
    handleShowHostsSetting() {
      this.applyHostsVisibility();
      this.persistSettings();
    },
    handleShowControllersSetting() {
      this.applyControllersVisibility();
      this.persistSettings();
    },
    applyLocaleSetting() {
      const locale = this.settings.language || "en";
      if (this.$i18n?.locale && this.$i18n.locale !== locale) {
        this.$i18n.locale = locale;
      }
    },
    handleLanguageChange() {
      this.applyLocaleSetting();
      this.persistSettings();
    },
    maybeShowFirstRunHelp() {
      try {
        const key = "mininetGuiHelpShown";
        const hasShown = localStorage.getItem(key);
        if (hasShown) return;
        localStorage.setItem(key, "true");
      } catch (error) {
        console.warn("Failed to persist first-run help flag", error);
      }
      this.handleOpenUsage();
    },
    getLinkOptionsPayload() {
      const opts = this.settings.linkOptions || {};
      const payload = {};
      if (opts.bw !== "" && opts.bw !== null && opts.bw !== undefined) payload.bw = Number(opts.bw);
      if (opts.delay !== "" && opts.delay !== null && opts.delay !== undefined) payload.delay = Number(opts.delay);
      if (opts.jitter !== "" && opts.jitter !== null && opts.jitter !== undefined) payload.jitter = Number(opts.jitter);
      if (opts.loss !== "" && opts.loss !== null && opts.loss !== undefined) payload.loss = Number(opts.loss);
      if (opts.max_queue_size !== "" && opts.max_queue_size !== null && opts.max_queue_size !== undefined) {
        payload.max_queue_size = Number(opts.max_queue_size);
      }
      if (opts.use_htb) payload.use_htb = true;
      return Object.keys(payload).length ? payload : null;
    },
    formatLinkTitle(options) {
      if (!options) return this.$t("link.noAttributes");
      const parts = [];
      if (options.bw !== undefined) parts.push(`bw: ${options.bw} Mbps`);
      if (options.delay !== undefined) parts.push(`delay: ${options.delay} ms`);
      if (options.jitter !== undefined) parts.push(`jitter: ${options.jitter} ms`);
      if (options.loss !== undefined) parts.push(`loss: ${options.loss} %`);
      if (options.max_queue_size !== undefined) parts.push(`queue: ${options.max_queue_size}`);
      if (options.use_htb) parts.push("htb: true");
      return parts.length ? parts.join(" | ") : this.$t("link.noAttributes");
    },
    formatPortLabel(intfs) {
      if (!intfs?.from || !intfs?.to) return "";
      return `${intfs.from} ↔ ${intfs.to}`;
    },
    hostLabel(host) {
      if (!host) return "";
      if (this.settings.showHostIp && host.ip) {
        return `${host.name}\n${host.ip}`;
      }
      return `${host.name}`;
    },
    switchLabel(sw) {
      if (!sw) return "";
      if (this.settings.showSwitchDpids) {
        const num = Number(String(sw.id || sw.name).replace(/^s/, ""));
        if (!Number.isNaN(num)) {
          return `${sw.name} <${this.intToDpid(num)}>`;
        }
      }
      return `${sw.name}`;
    },
    controllerLabel(ctl) {
      if (!ctl) return "";
      const controllerType = (ctl.controller_type || "").toLowerCase();
      const isRyu = controllerType === "ryu";
      const isRemote = ctl.remote || controllerType === "remote";
      if (isRemote || isRyu) {
        const targetParts = [];
        if (ctl.ip) targetParts.push(ctl.ip);
        if (ctl.port) targetParts.push(String(ctl.port));
        const target = targetParts.length ? ` <${targetParts.join(":")}>` : "";
        const parts = [`${ctl.name}${target}`];
        if (isRyu && ctl.ryu_app) {
          parts.push(`[ryu:${ctl.ryu_app}]`);
        }
        return parts.join(" ");
      }
      return `${ctl.name}`;
    },
    controllerColor() {
      return this.nodeBaseColor();
    },
    controllerIconColor(nodeOrColorCode) {
      if (this.isLightTheme) {
        return "#000000";
      }
      const colorCode = typeof nodeOrColorCode === "string" ? nodeOrColorCode : nodeOrColorCode?.colorCode;
      return colorCode || "#ffffff";
    },
    controllerImageForColor(colorCode) {
      const fill = colorCode || "#ffffff";
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36"><path d="M26.5,2h-17C8.7,2,8,2.7,8,3.5V34h20V3.5C28,2.7,27.3,2,26.5,2z M18,30.5c-1.5,0-2.8-1.2-2.8-2.8S16.5,25,18,25s2.8,1.2,2.8,2.8S19.5,30.5,18,30.5z M23,22.6H13V21h10V22.6z M24,11.6H12V10h12V11.6z M24,7.6H12V6h12V7.6z" fill="${fill}"/><circle cx="18" cy="27.8" r="1.2" fill="${fill}"/></svg>`;
      return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
    },
    applyHostLabels() {
      Object.values(this.hosts || {}).forEach((host) => {
        const label = this.hostLabel(host);
        host.label = label;
        this.nodes.update({ id: host.id, label });
      });
    },
    applySwitchLabels() {
      Object.values(this.switches || {}).forEach((sw) => {
        const label = this.switchLabel(sw);
        sw.label = label;
        this.nodes.update({ id: sw.id, label });
      });
    },
    applyHostsVisibility() {
      this.hostsHidden = !this.settings.showHosts;
      if (!this.nodes || !this.nodes.forEach) return;
      this.nodes.forEach((node) => {
        if (node.type === "host") {
          node.hidden = this.hostsHidden;
          this.nodes.updateOnly(node);
        }
      });
    },
    applyControllersVisibility() {
      this.controllersHidden = !this.settings.showControllers;
      if (!this.nodes || !this.nodes.forEach) return;
      this.nodes.forEach((node) => {
        if (node.type === "controller") {
          node.hidden = this.controllersHidden;
          this.nodes.updateOnly(node);
        }
      });
    },
    applyVisibilitySettings() {
      this.applyHostsVisibility();
      this.applyControllersVisibility();
    },
    applyPortLabels() {
      if (!this.edges || !this.edges.forEach) return;
      const showLabels = !!this.settings.showPortLabels;
      const updates = [];
      this.edges.forEach((edge) => {
        const update = this.buildPortLabelUpdate(edge, showLabels);
        if (update) {
          updates.push(update);
        }
      });
      if (updates.length) {
        this.edges.update(updates);
      }
    },
    buildPortLabelUpdate(edge, showLabels) {
      if (!edge || !edge.id) return null;
      const update = { id: edge.id, label: "" };
      if (!showLabels) return update;
      const label = this.formatPortLabel(edge.intfs);
      if (!label) return update;
      update.label = label;
      update.font = {
        ...(edge.font || {}),
        align: "horizontal",
        size: 10,
        color: this.portLabelFontColor(),
      };
      return update;
    },
    showSettingsModal() {
      this.closeAllActiveModes();
      this.modalHeader = this.$t("menu.settings");
      this.modalOption = "settings";
      this.showModal = true;
    },
    computeNetwork() {
      if (this.network)
        return this.network;
      return new Network(this.$refs.graph, { nodes: this.nodes, edges: this.edges }, buildOptions(this.settings.theme));
    },
    async setupNetwork() {
      await this.refreshBackendHealth();
      this.hosts = await getHosts();
      this.switches = await getSwitches();
      this.controllers = await getControllers();
      this.nats = await getNats();
      this.routers = await getRouters();

      Object.values(this.hosts).map((host) => {
        host.shape = "circularImage";

        host.color = this.nodeBaseColor();
        host.image = this.currentAssets().host;
        host.label = this.hostLabel(host);
        host.hidden = this.hostsHidden;
        return host;
      });

      Object.values(this.switches).map((sw) => {
        sw.shape = "circularImage";
        sw.color = this.nodeBaseColor();
        sw.image = this.switchImageForType(sw.switch_type);
        sw.label = this.switchLabel(sw);
        return sw;
      });

      Object.values(this.controllers).map((ctl) => {
        ctl.shape = "circularImage";
        ctl.colorCode = ctl.color || "#ffffff";
        ctl.color = this.controllerColor();
        ctl.image = this.controllerImageForColor(this.controllerIconColor(ctl));
        ctl.label = this.controllerLabel(ctl);
        ctl.hidden = this.controllersHidden;
        return ctl;
      });

      Object.values(this.nats).map((nat) => {
        nat.shape = "circularImage";
        nat.color = this.nodeBaseColor();
        nat.image = this.currentAssets().nat;
        nat.label = nat.name || nat.id;
        return nat;
      });

      Object.values(this.routers).map((router) => {
        router.shape = "circularImage";
        router.color = this.nodeBaseColor();
        router.image = this.currentAssets().router;
        router.label = router.name || router.id;
        return router;
      });

      this.links = await getEdges();
      for (const link of this.links) {
        const options = link.options || null;
        const intfs = link.intfs || null;
        this.edges.add({
          from: link.from,
          to: link.to,
          color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor(),
          title: this.formatLinkTitle(options),
          options,
          intfs,
        });
      }
      for (const sw in this.switches) {
        let ctl = this.switches[sw].controller;
        if (ctl)
          this.edges.add({
            from: sw,
            to: ctl,
            color: this.controllerLinkColor(),
            dashes: [10, 10]
          });
      }

      const initialNodes = [
        ...Object.values(this.hosts),
        ...Object.values(this.switches),
        ...Object.values(this.controllers),
        ...Object.values(this.nats),
        ...Object.values(this.routers),
      ];
      this.nodes.clear();
      this.nodes.add(initialNodes);
      this.applyVisibilitySettings();
      this.selectInitialWebshell();
      this.applyPortLabels();
      console.log("network inside mounted, before setup:", this.network);
      this.network.setOptions({
        manipulation: {
          enabled: false,
          addEdge: async (data, callback) => {
            if (data.from == data.to) {
              alert(this.$t("errors.connectSelf"));
              return;
            }
            console.log("network", this.network);
            let from = this.nodes.get(data.from);
            let to = this.nodes.get(data.to);
            if (from.type === "controller" && to.type === "controller") {
                alert(this.$t("errors.controllerToController"));
                return;
            } else if (from.type === "host" && this.hostHasLink(from.id)) {
                alert(this.$t("errors.hostHasLink"));
                return;
            } else if (to.type === "host" && this.hostHasLink(to.id)) {
                alert(this.$t("errors.hostHasLink"));
                return;
            } else if (from.type === "controller" || to.type === "controller") {
                if (from.type === "host" || to.type === "host") {
                    alert(this.$t("errors.hostToController"));
                    return;
                }
                let [sw, ctl] = (from.type === "controller") ? [to, from] : [from, to];
                sw.controller = ctl.id;
                await assocSwitch(sw.id, ctl.id);
                data.color = { color: this.controllerLinkColor() };
                data.dashes = [10, 10];
            } else {
              const options = this.getLinkOptionsPayload();
              let link = await deployLink(data.from, data.to, options);
              data.id = link.id;
              data.color = { color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor() };
              data.title = this.formatLinkTitle(options);
              data.options = options;
              data.intfs = link?.intfs || null;
            }
            callback(data);
            this.enterAddEdgeMode();
            this.applyPortLabels();
          },
          deleteNode: async (data, callback) => {
            console.log("node deletion", data);
            let results = [];
            for (const nodeId of data.nodes) {
              try {
                await deleteNode(nodeId);
                results.push(nodeId);
              } catch (error) {
                console.log("error deleting node", nodeId, error);
              }
            }
            data.nodes = results;
            callback(data);
          },
          deleteEdge: async (data, callback) => {
            try {
              const results = [];
              for (const edge of data.edges) {
                  let link = this.edges.get(edge);
                  let src = this.nodes.get(link.from);
                  let dst = this.nodes.get(link.to);
                  console.log("src", src);
                  console.log("dst", dst);
                  if (src.type == "controller" || dst.type == "controller") {
                    await removeAssociation(link.from, link.to);
                  } else {
                    await deleteLink(link.from, link.to);
                  }
                  results.push(link.id);
              }
              console.log("All edges deleted:", results);
              data.edges = results;
              callback(data);
            } catch (error) {
              console.error("Error deleting edges:", error);
            }
          },
        },
      });
      this.network.on("doubleClick", async (event) => {
        if (event.nodes.length === 1) {
          this.showStatsModal(event.nodes[0]);
          return;
        }
        if (event.edges.length === 1) {
          this.showLinkModal(event.edges[0]);
        }
      });
      this.network.on("oncontext", (event) => {
        if (event?.event?.preventDefault) {
          event.event.preventDefault();
        }
        const pointer = event?.pointer?.DOM;
        const nodeId = pointer ? this.network.getNodeAt(pointer) : event?.nodes?.[0];
        if (!nodeId) {
          this.hideContextMenu();
          return;
        }
        this.network.unselectAll();
        this.network.selectNodes([nodeId], false);
        const clientX = event?.event?.clientX ?? 0;
        const clientY = event?.event?.clientY ?? 0;
        this.contextMenu = {
          visible: true,
          x: clientX,
          y: clientY,
          nodeId,
        };
      });
      this.network.on("click", () => {
        this.hideContextMenu();
      });
      this.network.on("dragEnd", async (event) => {
        this.handleNodeDragEnd(event);
      });
    },
    async refreshBackendHealth() {
      try {
        const health = await getHealthStatus();
        if (health) {
          this.mininetConnected = !!health.connected;
          this.networkStarted = !!health.network_started;
        } else {
          this.mininetConnected = false;
          this.networkStarted = false;
        }
      } catch (error) {
        console.warn("Could not refresh backend health", error);
        this.mininetConnected = false;
        this.networkStarted = false;
      }
      this.updateLinkColors();
    },
    updateLinkColors() {
      if (!this.edges?.forEach) return;
      const colorValue = this.networkStarted ? "#00aa00ff" : this.linkInactiveColor();
      const updates = [];
      this.edges.forEach((edge) => {
        if (edge?.dashes?.length) return;
        const currentColor = edge.color;
        const normalizedColor =
          typeof currentColor === "object" && currentColor !== null && "color" in currentColor
            ? { ...currentColor, color: colorValue }
            : colorValue;
        updates.push({ id: edge.id, color: normalizedColor });
      });
      if (updates.length) {
        this.edges.update(updates);
        if (this.network) {
          this.network.redraw();
        }
      }
    },
    selectInitialWebshell() {
      this.webshellFocusId = null;
      this.webshellView = "logs";
    },
    getLowestNodeId(ids) {
      return [...ids].sort(this.compareNodeIds)[0];
    },
    compareNodeIds(a, b) {
      const parse = (value) => {
        const match = String(value).match(/^([a-zA-Z]+)(\d+)$/);
        if (!match) return { prefix: String(value), num: Number.MAX_SAFE_INTEGER };
        return { prefix: match[1], num: Number(match[2]) };
      };
      const pa = parse(a);
      const pb = parse(b);
      if (pa.prefix === pb.prefix) return pa.num - pb.num;
      return pa.prefix.localeCompare(pb.prefix);
    },
    openWebshellForNode(nodeId) {
      if (!nodeId) return;
      const nextCount = (this.terminalSessionCounters[nodeId] || 0) + 1;
      this.terminalSessionCounters = {
        ...this.terminalSessionCounters,
        [nodeId]: nextCount,
      };
      const sessionId = `${nodeId}-${nextCount}-${Date.now()}`;
      const label = `${nodeId}(${nextCount})`;
      this.terminalSessions = [
        ...this.terminalSessions,
        { id: sessionId, nodeId, label },
      ];
      this.webshellView = "terminal";
      this.webshellFocusId = null;
      this.$nextTick(() => {
        this.webshellFocusId = sessionId;
      });
    },
    hideContextMenu() {
      if (!this.contextMenu.visible) return;
      this.contextMenu = {
        visible: false,
        x: 0,
        y: 0,
        nodeId: null,
      };
    },
    openWebshellFromMenu() {
      const nodeId = this.contextMenu.nodeId;
      this.hideContextMenu();
      this.openWebshellForNode(nodeId);
    },
    openNodeStatsFromMenu() {
      const nodeId = this.contextMenu.nodeId;
      this.hideContextMenu();
      if (nodeId) this.showStatsModal(nodeId);
    },
    handleCloseSession(sessionId) {
      this.terminalSessions = this.terminalSessions.filter(session => session.id !== sessionId);
    },
    handleWebshellViewChange(view) {
      this.webshellActiveView = view;
    },
    hostHasLink(hostId) {
      const edges = this.edges?.get ? this.edges.get() : [];
      return edges.some((edge) => edge.from === hostId || edge.to === hostId);
    },
    async createLinkBetween(fromId, toId) {
      const fromNode = this.nodes.get(fromId);
      const toNode = this.nodes.get(toId);
      if (!fromNode || !toNode) {
        throw new Error("Invalid node ids for link.");
      }
      const options = this.getLinkOptionsPayload();
      const link = await deployLink(fromId, toId, options);
      const [edgeId] = this.edges.add({
        from: fromId,
        to: toId,
        color: { color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor() },
        title: this.formatLinkTitle(options),
        options,
        intfs: link?.intfs || null,
      });
      this.applyPortLabels();
      return link;
    },
    async llmCreateHost({ nodes } = {}) {
      if (!Array.isArray(nodes) || nodes.length === 0) {
        throw new Error("nodes array is required.");
      }
      const created = [];
      for (const entry of nodes) {
        if (!Number.isFinite(entry?.x) || !Number.isFinite(entry?.y)) {
          throw new Error("Each node requires numeric x and y.");
        }
        const host = await this.createHost({ x: entry.x, y: entry.y });
        created.push(host.id);
      }
      return { ids: created };
    },
    async llmCreateSwitch({ nodes } = {}) {
      if (!Array.isArray(nodes) || nodes.length === 0) {
        throw new Error("nodes array is required.");
      }
      const created = [];
      for (const entry of nodes) {
        if (!Number.isFinite(entry?.x) || !Number.isFinite(entry?.y)) {
          throw new Error("Each node requires numeric x and y.");
        }
        const sw = await this.createSwitch({ x: entry.x, y: entry.y });
        created.push(sw.id);
      }
      return { ids: created };
    },
    async llmCreateController({ nodes } = {}) {
      if (!Array.isArray(nodes) || nodes.length === 0) {
        throw new Error("nodes array is required.");
      }
      const created = [];
      for (const entry of nodes) {
        if (!Number.isFinite(entry?.x) || !Number.isFinite(entry?.y)) {
          throw new Error("Each node requires numeric x and y.");
        }
        const remote = Boolean(entry?.remote);
        const ip = remote ? entry?.ip : null;
        const port = remote ? entry?.port : null;
        const controllerType = entry?.controller_type || (remote ? "remote" : "default");
        const ryuApp = controllerType === "ryu" ? entry?.ryu_app : null;
        await this.createController({ x: entry.x, y: entry.y }, remote, ip, port, controllerType, ryuApp);
        const lastId = Object.keys(this.controllers).sort(this.compareNodeIds).pop();
        if (lastId) created.push(lastId);
      }
      return { ids: created };
    },
    async llmCreateLink({ from, to } = {}) {
      if (!from || !to) throw new Error("from and to are required.");
      const link = await this.createLinkBetween(from, to);
      return { from: link.from ?? from, to: link.to ?? to };
    },
    async llmAssociateSwitch({ switch_id, controller_id } = {}) {
      if (!switch_id || !controller_id) throw new Error("switch_id and controller_id are required.");
      await assocSwitch(switch_id, controller_id);
      this.edges.add({
        from: switch_id,
        to: controller_id,
        color: { color: this.controllerLinkColor() },
        dashes: [10, 10],
      });
      if (this.switches[switch_id]) {
        this.switches[switch_id].controller = controller_id;
      }
      return { ok: true };
    },
    async llmGetTopology() {
      const nodes = [
        ...Object.values(this.hosts || {}),
        ...Object.values(this.switches || {}),
        ...Object.values(this.controllers || {}),
      ].map((node) => ({
        id: node.id,
        type: node.type,
        name: node.name,
        label: node.label,
        ip: node.ip,
        controller: node.controller,
      }));
      const edges = (this.edges?.get ? this.edges.get() : []).map((edge) => ({
        from: edge.from,
        to: edge.to,
        title: edge.title,
        dashes: edge.dashes,
        color: edge.color,
      }));
      return { nodes, edges };
    },
    async llmRunCommand({ node_id, command } = {}) {
      if (!node_id || !command) throw new Error("node_id and command are required.");
      const wsUrl = `${import.meta.env.VITE_BACKEND_WS_URL}/api/mininet/terminal/${node_id}`;
      return await new Promise((resolve, reject) => {
        const ws = new WebSocket(wsUrl);
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error("Command timed out."));
        }, 4000);
        ws.onopen = () => {
          ws.send(command + "\n");
          setTimeout(() => {
            clearTimeout(timeout);
            ws.close();
            resolve({ ok: true });
          }, 300);
        };
        ws.onerror = () => {
          clearTimeout(timeout);
          reject(new Error("WebSocket error while running command."));
        };
      });
    },
    async llmDeleteNode({ node_id } = {}) {
      if (!node_id) throw new Error("node_id is required.");
      await deleteNode(node_id);
      this.nodes.remove(node_id);
      delete this.hosts[node_id];
      delete this.switches[node_id];
      delete this.controllers[node_id];
      delete this.nats[node_id];
      delete this.routers[node_id];
      return { deleted: node_id };
    },
    intToDpid (number) {
      return number.toString(16).padStart(16, '0').replace(/(..)(..)(..)(..)(..)(..)(..)(..)/, '$1:$2:$3:$4:$5:$6:$7:$8');
    },
    async createHost(position) {
      let hostId = Object.values(this.hosts).length + 1;
      while (`h${hostId}` in this.hosts) {
        hostId++;
      }
      let host = {
        id: `h${hostId}`,
        type: "host",
        name: `h${hostId}`,
        label: null,
        ip: `10.0.0.${hostId}/8`,
        mac: hostId.toString(16).toUpperCase().padStart(12, "0"),
        shape: "circularImage",
        color: this.nodeBaseColor(),
      };
      host.label = this.hostLabel(host);
      host.image = this.currentAssets().host;
      host.hidden = !this.settings.showHosts;
      if (position) {
        host.x = position.x;
        host.y = position.y;
      }
      if (await deployHost(host)) {
        this.nodes.add(host);
        this.hosts[host.name] = host;
      } else {
        throw "Could not create host " + hostId;
      }
      return host;
    },
    async createRouter(position) {
      let routerId = Object.values(this.routers).length + 1;
      while (`r${routerId}` in this.routers) {
        routerId++;
      }
      const octet = 100 + routerId;
      let router = {
        id: `r${routerId}`,
        type: "router",
        name: `r${routerId}`,
        label: `r${routerId}`,
        ip: `10.0.0.${octet}/8`,
        mac: octet.toString(16).toUpperCase().padStart(12, "0"),
        shape: "circularImage",
        color: this.nodeBaseColor(),
      };
      router.image = this.currentAssets().router;
      if (position) {
        router.x = position.x;
        router.y = position.y;
      }
      if (await deployRouter(router)) {
        this.nodes.add(router);
        this.routers[router.name] = router;
      } else {
        throw "Could not create router " + routerId;
      }
      return router;
    },
    async createNat(position) {
      let natId = Object.values(this.nats).length + 1;
      while (`nat${natId}` in this.nats) {
        natId++;
      }
      const octet = 200 + natId;
      let nat = {
        id: `nat${natId}`,
        type: "nat",
        name: `nat${natId}`,
        label: `nat${natId}`,
        ip: `10.0.0.${octet}/8`,
        mac: octet.toString(16).toUpperCase().padStart(12, "0"),
        shape: "circularImage",
        color: this.nodeBaseColor(),
      };
      nat.image = this.currentAssets().nat;
      if (position) {
        nat.x = position.x;
        nat.y = position.y;
      }
      if (await deployNat(nat)) {
        this.nodes.add(nat);
        this.nats[nat.name] = nat;
      } else {
        throw "Could not create NAT " + natId;
      }
      return nat;
    },
    async createSwitch(switchData) {
      let swId = Object.values(this.switches).length + 1;
      while (`s${swId}` in this.switches) {
        swId++;
      }
      const switchType = switchData?.switch_type || "ovskernel";
      const defaultOpenflow = this.settings.switchOpenflow || "";
      const rawOfVersion = (switchData?.of_version ?? defaultOpenflow) || null;
      const isOvsType = ["ovs", "ovskernel", "ovsbridge"].includes(String(switchType || "").toLowerCase());
      const ofVersion = isOvsType ? rawOfVersion : null;
      let sw = {
        id: `s${swId}`,
        type: "sw",
        name: `s${swId}`,
        label: switchData.label || null,
        ports: switchData.ports || 4,
        controller: null,
        switch_type: switchType,
        of_version: ofVersion,
        shape: "circularImage",
        color: this.nodeBaseColor(),
      };
      sw.label = this.switchLabel(sw);
      sw.image = this.switchImageForType(sw.switch_type);
      if (switchData) {
        sw.x = switchData.x;
        sw.y = switchData.y;
      }
      if (await deploySwitch(sw)) {
        this.nodes.add(sw);
        this.switches[sw.name] = sw;
      } else {
        throw "Could not create sw " + swId;
      }
      if (switchData.controller && await assocSwitch(sw.id, switchData.controller)) {
        this.switches[sw.name].controller = switchData.controller;
        this.edges.add({
          from: sw.id,
          to: switchData.controller,
          color: { color: this.controllerLinkColor() },
          dashes: [10, 10]
        });
      }
      return sw;
    },
    async showControllerFormModal(position, presetType = null) {
      this.modalHeader = this.$t("controller.formTitle");
      this.modalOption = "controllerForm";
      this.showModal = true;
      this.controllerFormPreset = presetType;
      this.controllerFormData = null;
      this.formData = null;

      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });

      console.log("GOT DATA:", this.formData);
      await this.createController(
        position,
        this.formData.type === "remote",
        this.formData.ip,
        this.formData.port,
        this.formData.type,
        this.formData.ryu_app,
        this.formData.color
      );
    },
    showControllerEditModal(controllerId) {
      const controller = this.controllers?.[controllerId] || (this.modalData?.id === controllerId ? this.modalData : null);
      if (!controller) return;
      this.modalHeader = this.$t("controller.editTitle", { id: controllerId });
      this.modalOption = "controllerForm";
      this.showModal = true;
      this.controllerFormPreset = null;
      this.controllerFormData = {
        ...controller,
        color: controller.colorCode || controller.color || "#ffffff",
      };
    },
    handleControllerFormSubmit(data) {
      this.formData = data;
      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }
      this.showModal = false;
    },
    async handleControllerFormUpdate(data) {
      if (!this.controllerFormData?.id) return;
      const controllerId = this.controllerFormData.id;
      const payload = {
        controller_type: data.type,
        remote: data.type === "remote",
        ip: data.ip,
        port: data.port,
        ryu_app: data.ryu_app,
        color: data.color,
      };
      const updated = await updateController(controllerId, payload);
      if (!updated) return;
      const existing = this.controllers[controllerId] || {};
      const colorCode = updated.color || data.color || existing.colorCode || "#ffffff";
      const merged = {
        ...existing,
        ...updated,
        colorCode,
        color: this.controllerColor(),
      };
      merged.label = this.controllerLabel(merged);
      merged.image = this.controllerImageForColor(colorCode);
      this.controllers[controllerId] = merged;
      this.nodes.update({
        id: controllerId,
        label: merged.label,
        ip: merged.ip,
        port: merged.port,
        ryu_app: merged.ryu_app,
        controller_type: merged.controller_type,
        color: merged.color,
        image: merged.image,
      });
      this.closeModal();
    },
    async createController(position, remote, ip, port, controllerType = "default", ryuApp = null, colorCode = null) {
      let ctlId = Object.values(this.controllers).length + 1;
      while (`c${ctlId}` in this.controllers) {
        ctlId++;
      }
      const isRyu = controllerType === "ryu";
      const effectiveIp = ip || (isRyu ? "127.0.0.1" : ip);
      const color = colorCode || "#ffffff";
      let ctl = {
        id: `c${ctlId}`,
        type: "controller",
        name: `c${ctlId}`,
        label: null,
        controller_type: controllerType,
        remote: remote,
        ip: effectiveIp,
        port: port,
        x: position.x,
        y: position.y,
        shape: "circularImage",
        color: this.controllerColor(),
        colorCode: color,
      };
      if (isRyu) ctl.ryu_app = ryuApp;
      ctl.label = this.controllerLabel(ctl);
      ctl.image = this.controllerImageForColor(color);
      ctl.hidden = !this.settings.showControllers;
      if (await deployController(ctl)) {
        this.nodes.add(ctl);
        this.controllers[ctl.name] = ctl;
      } else {
        throw "Could not create controller " + ctlId;
      }
    },
    handleDrop(event) {
      this.closeAllActiveModes();
      event.preventDefault();
      console.log("drop event triggered, text/plain", event.dataTransfer.getData("text/plain"));
      var data = event.dataTransfer.getData("text/plain");
      const rect = this.$refs.graph.getBoundingClientRect();
      const domPoint = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      if (data === "draggable-host") {
        this.createHost(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-router") {
        this.createRouter(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-switch") {
        this.createSwitch(
          this.network.DOMtoCanvas(domPoint),
        );
      } else if (data === "draggable-switch-ovs") {
        this.createSwitch({
          ...this.network.DOMtoCanvas(domPoint),
          switch_type: "ovs",
        });
      } else if (data === "draggable-switch-ovsbridge") {
        this.createSwitch({
          ...this.network.DOMtoCanvas(domPoint),
          switch_type: "ovsbridge",
        });
      } else if (data === "draggable-switch-user") {
        this.createSwitch({
          ...this.network.DOMtoCanvas(domPoint),
          switch_type: "user",
        });
      } else if (data === "draggable-controller-default") {
        this.createController(
          this.network.DOMtoCanvas(domPoint),
          false,
          null,
          null,
          "default"
        );
      } else if (data === "draggable-controller-remote") {
        this.showControllerFormModal(
          this.network.DOMtoCanvas(domPoint),
          "remote"
        );
      } else if (data === "draggable-controller-ryu") {
        this.showControllerFormModal(
          this.network.DOMtoCanvas(domPoint),
          "ryu"
        );
      } else if (data === "draggable-controller-nox") {
        this.createController(
          this.network.DOMtoCanvas(domPoint),
          false,
          null,
          null,
          "nox"
        );
      } else if (data === "draggable-nat") {
        this.createNat(
          this.network.DOMtoCanvas(domPoint),
        );
      }
    },
    async handleNodeDragEnd(event) {
      event.nodes.forEach(async nodeId => {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) return;
        let node = this.network.body.nodes[nodeId];
        await updateNodePosition(nodeId, [node.x, node.y]);
      });
    },
    enterAddEdgeMode() {
      this.addEdgeMode = true;
      this.network.addEdgeMode();
    },
    closeAddEdgeMode() {
      this.addEdgeMode = false;
      this.network.disableEditMode();
    },
    closeModal() {
      this.modalHeader = "";
      this.showModal = false;
      this.modalOption = null;
      this.modalData = null;
      this.linkModalEdgeId = null;
      this.controllerFormPreset = null;
      this.controllerFormData = null;
      this.formData = null;
      this.iperfError = "";
      this.iperfResult = null;
    },
    closeAllActiveModes() {
      this.closeAddEdgeMode();
      this.closeModal();
      this.hideContextMenu();
    },
    handleToggleAddEdgeMode() {
      console.log("addedgemode toggle");
      if (!this.addEdgeMode) {
        this.enterAddEdgeMode();
      } else {
        this.closeAddEdgeMode();
      }
    },
    toggleShowHosts() {
      this.settings.showHosts = !this.settings.showHosts;
      this.applyHostsVisibility();
      this.persistSettings();
    },
    toggleShowControllers () {
      this.settings.showControllers = !this.settings.showControllers;
      this.applyControllersVisibility();
      this.persistSettings();
    },
    async doDeleteSelected() {
      this.closeAllActiveModes();
      this.network.deleteSelected();
    },
    doSelectAll() {
      console.log("CTRL A PRESSED");
      this.closeAllActiveModes();
      const ids = this.nodes.getIds();
      this.network.setSelection({nodes: ids});
    },
    async showPingallModal() {
      if (this.pingallRunning) return;
      this.closeAllActiveModes();
      this.pingallRunning = true;

      let pingallResults = await requestRunPingall();
      if (pingallResults && pingallResults.running) {
        this.pingallRunning = false;
        return;
      } else {
      this.modalHeader = this.$t("pingall.resultsTitle");
        this.modalOption = "pingall";
        this.modalData = pingallResults || null;
        this.showModal = true;
      }
      this.pingallRunning = false;
    },
    showIperfModal() {
      if (this.iperfBusy) return;
      this.closeAllActiveModes();
      const hostIds = Object.keys(this.hosts || {});
      this.iperfForm.client = hostIds[0] || "";
      this.iperfForm.server = hostIds[1] || "";
      this.iperfForm.l4_type = "TCP";
      this.iperfForm.seconds = 5;
      this.iperfForm.udp_bw = "";
      this.iperfForm.fmt = "";
      this.iperfForm.port = "";
      this.iperfError = "";
      this.iperfResult = null;
      this.iperfTab = "config";
      this.modalHeader = this.$t("menu.runIperf");
      this.modalOption = "iperf";
      this.showModal = true;
    },
    async runIperfTest() {
      if (!this.iperfForm.client || !this.iperfForm.server) return;
      if (this.iperfForm.client === this.iperfForm.server) {
        this.iperfError = this.$t("iperf.errorDifferentHosts");
        return;
      }
      this.closeModal();
      this.iperfBusy = true;
      this.iperfError = "";
      this.iperfResult = null;
      const payload = {
        client: this.iperfForm.client,
        server: this.iperfForm.server,
        l4_type: this.iperfForm.l4_type,
      };
      if (this.iperfForm.seconds) payload.seconds = Number(this.iperfForm.seconds);
      if (this.iperfForm.port) payload.port = Number(this.iperfForm.port);
      if (this.iperfForm.fmt) payload.fmt = this.iperfForm.fmt;
      if (this.iperfForm.l4_type === "UDP" && this.iperfForm.udp_bw) {
        payload.udp_bw = this.iperfForm.udp_bw;
      }
      const result = await runIperf(payload);
      if (result?.running) {
        this.iperfError = this.$t("iperf.errorAlreadyRunning");
        this.iperfBusy = false;
        this.modalHeader = this.$t("menu.runIperf");
        this.modalOption = "iperf";
        this.iperfTab = "config";
        this.showModal = true;
        return;
      }
      if (!result) {
        this.iperfError = this.$t("iperf.errorFailed");
      } else {
        this.iperfResult = result;
      }
      this.iperfBusy = false;
      this.modalHeader = this.$t("iperf.resultsTitle");
      this.modalOption = "iperf";
      this.iperfTab = "results";
      this.showModal = true;
    },
    formatIperfResult(result) {
      if (!result) return "";
      if (result.client && result.server) {
        return `${this.$t("iperf.client")}: ${result.client}\n${this.$t("iperf.server")}: ${result.server}`;
      }
      return JSON.stringify(result, null, 2);
    },
    async showStatsModal(nodeId) {
      this.closeAllActiveModes();
      this.modalHeader = this.$t("node.infoTitle", { id: nodeId });
      this.modalOption = "nodeStats";
      let nodeStats = await getNodeStats(nodeId);
      console.log("nodeStats", nodeStats);
      this.modalData = nodeStats || null;
      this.showModal = true;
    },
    showLinkModal(edgeId) {
      if (!edgeId) return;
      const link = this.edges.get(edgeId);
      if (!link?.from || !link?.to) return;
      const srcNode = this.nodes.get(link.from);
      const dstNode = this.nodes.get(link.to);
      if (srcNode?.type === "controller" || dstNode?.type === "controller") {
        return;
      }
      this.closeAllActiveModes();
      this.modalHeader = this.$t("link.infoTitle", { from: link.from, to: link.to });
      this.modalOption = "linkStats";
      this.modalData = {
        from: link.from,
        to: link.to,
        options: link.options || null,
      };
      this.linkModalEdgeId = edgeId;
      this.showModal = true;
    },
    handleLinkUpdated(options) {
      if (!this.linkModalEdgeId) return;
      this.edges.update({
        id: this.linkModalEdgeId,
        options,
        title: this.formatLinkTitle(options),
      });
      if (this.modalOption === "linkStats") {
        this.modalData = { ...this.modalData, options };
      }
      this.applyPortLabels();
    },
    handleHostUpdated(updatedHost) {
      if (!updatedHost?.id) return;
      const existing = this.hosts[updatedHost.id];
      if (existing) {
        existing.ip = updatedHost.ip;
        this.hosts[updatedHost.id] = existing;
        this.nodes.update({ id: updatedHost.id, ip: updatedHost.ip, label: this.hostLabel(existing) });
      }
      if (this.modalOption === "nodeStats") {
        this.modalData = updatedHost;
      }
    },
    async createSingleTopo(nDevices, controller) {
      let newSw = await this.createSwitch({x: 250, y: 150, controller: controller});
      for (var i=0; i<nDevices; i++) {
        let newHost = await this.createHost({x: 200+i*90, y: 300});
        let link = await deployLink(newSw.id, newHost.id);
        this.edges.add({
          from: newSw.id,
          to: newHost.id,
          color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor(),
          intfs: link?.intfs || null,
        });
      }
      this.applyPortLabels();
    },
    async createLinearTopo(nDevices, nHosts, controller) {
      let prevSw = null;
      for (let i = 0; i < nDevices; i++) {
        let newSw = await this.createSwitch({ x: 250 + i * 90, y: 150, controller: controller});
        console.log("newSw", newSw);

        for (let j = 0; j < nHosts; j++) {
          let newHost = await this.createHost({ x: 200 + i * 90, y: 300 + j * 50 });
          console.log("newHost", newHost);

          const link = await deployLink(newSw.id, newHost.id);
          this.edges.add({
            from: newSw.id,
            to: newHost.id,
            color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor(),
            intfs: link?.intfs || null,
          });
        }

        if (prevSw) {
          const link = await deployLink(newSw.id, prevSw.id);
          this.edges.add({
            from: newSw.id,
            to: prevSw.id,
            color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor(),
            intfs: link?.intfs || null,
          });
        }
        prevSw = newSw;
      }
      this.applyPortLabels();
    },
    async createTreeTopo(depth, fanout, controller) {
      const nodes = [];
      const maxNodes = Math.pow(fanout, depth);
      for (let d = depth; d >= 0; d--) {
        const layer = [];
        const numNodes = Math.pow(fanout, d);
        for (let i = 0; i < numNodes; i++) {
          let x = (i + 0.5) * maxNodes * 100 / (numNodes || 1);
          let y = 150 + d * 150;
          let node;
          if (d === depth) {
            node = await this.createHost({ x, y });
            console.log("Created Host:", node);
          } else {
            node = await this.createSwitch({ x: x, y: y, controller: controller});
            console.log("Created Switch:", node);
            const startIndex = i * fanout;
            const endIndex = startIndex + fanout;
            for (let j = startIndex; j < endIndex && j < nodes[d + 1].length; j++) {
              const child = nodes[d + 1][j];
              const link = await deployLink(node.id, child.id);
              this.edges.add({
                from: node.id,
                to: child.id,
                color: this.networkStarted ? "#00aa00ff" : this.linkInactiveColor(),
                intfs: link?.intfs || null,
              });
            }
          }
          layer.push(node);
        }
        nodes[d] = layer;
      }
      this.applyPortLabels();
    },
    async showTopologyFormModal() {
      this.modalHeader = this.$t("topology.createTitle");
      this.modalOption = "topologyForm";
      this.showModal = true;

      const result = await new Promise((resolve) => {
        this.modalPromiseResolve = resolve;
      });

      console.log("GOT DATA", this.formData);
      await this.handleCreateTopology(this.formData.type, this.formData.nDevices, this.formData.nLayers, this.formData.controller);
    },
    handleTopologyFormSubmit(data) {
      this.formData = data;
      console.log("FORM DATA", this.formData);

      if (this.modalPromiseResolve) {
        this.modalPromiseResolve(data);
        this.modalPromiseResolve = null;
      }
      this.showModal = false;
    },
    async handleCreateTopology(topologyType, nDevices, nLayers, controller){
      console.log("Received createTopology event with:", topologyType, "data", nDevices, nLayers);
      if (topologyType == "Single") {
        await this.createSingleTopo(nDevices, controller);
      } else if (topologyType == "Linear") {
        await this.createLinearTopo(nDevices, nLayers, controller);
      } else if (topologyType == "Tree") {
        await this.createTreeTopo(nLayers, nDevices, controller);
      }
    },
    async resetTopology() {
      if (await requestFullResetNetwork()) {
        this.snifferActive = false;
        console.log("Resetting topology");
        this.clearGraphState();
        await this.refreshBackendHealth();
      }
    },
    clearGraphState() {
      this.hosts = {};
      this.switches = {};
      this.controllers = {};
      this.nats = {};
      this.routers = {};
      this.links = [];
      this.nodes = new DataSet();
      this.edges = new DataSet();
      if (this.network) {
        this.network.setData({ nodes: this.nodes, edges: this.edges });
        this.network.redraw();
      }
    },
    handleSidebarToggle(isActive) {
      this.sidebarCollapsed = !isActive;
    },
    handleWebshellMinimizeChange(isMinimized) {
      this.webshellMinimized = !!isMinimized;
    },
    async toggleSniffer() {
      try {
        if (this.snifferActive) {
          const response = await stopSniffer();
          this.snifferActive = !!response.active;
        } else {
          const response = await startSniffer();
          this.snifferActive = !!response.active;
        }
      } catch (error) {
        this.snifferActive = false;
      }
    },
    async syncSnifferState() {
      try {
        const state = await getSnifferState();
        this.snifferActive = !!state.active;
      } catch (error) {
        // keep previous state; backend may not be ready yet
      }
    },
    async exportSniffer() {
      try {
        const blob = await exportSnifferPcap();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "sniffer.pcap";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Failed to export sniffer", error);
      }
    },
    exportTopologyAsPng() {
      try {
        const canvas = this.$refs.graph?.querySelector?.("canvas");
        if (!canvas) return;
        const dataUrl = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.href = dataUrl;
        link.download = "topology.png";
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error("Failed to export topology PNG", error);
        alert(this.$t("errors.exportPng"));
      }
    },
    showResetConfirmModal() {
      this.modalHeader = this.$t("confirm.resetTopologyTitle");
      this.modalOption = "confirmReset";
      this.modalData = null;
      this.showModal = true;
    },
    async confirmResetTopology() {
      await this.resetTopology();
      this.closeModal();
    },
    async exportTopology() {
      await requestExportNetwork();
    },
    async saveTopologyAs() {
      const payload = this.buildTopologyExportPayload();
      const jsonData = JSON.stringify(payload, null, 2);
      const fileName = "topology.json";

      if ("showSaveFilePicker" in window) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: fileName,
            types: [
              {
                description: "JSON",
                accept: { "application/json": [".json"] },
              },
            ],
          });
          const writable = await handle.createWritable();
          await writable.write(jsonData);
          await writable.close();
          return;
        } catch (error) {
          if (error?.name === "AbortError") return;
        }
      }

      const blob = new Blob([jsonData], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
    async exportMininetScript() {
      await requestExportMininetScript();
    },
    async exportAddressingPlan() {
      try {
        const plan = await getAddressingPlan();
        const createdAt = new Date().toLocaleString();
        const nodes = plan?.nodes || [];
        const doc = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
        doc.text(this.$t("addressing.title"), 40, 40);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        doc.text(this.$t("addressing.createdIn", { date: createdAt }), 40, 60);
        doc.text(this.$t("addressing.repository", { repo: "https://github.com/latarc/mininet-gui" }), 40, 74);

        const body = [];
        nodes.forEach((node) => {
          if (!node.intfs || node.intfs.length === 0) {
            body.push([node.id, node.type, "-", "-", "-", "-"]);
            return;
          }
          node.intfs.forEach((intf, idx) => {
            const ipv4 = (intf.ipv4 || []).join("\n");
            const ipv6 = (intf.ipv6 || []).join("\n");
            const mac = intf.mac || "";
            const row = [
              idx === 0 ? node.id : "",
              idx === 0 ? node.type : "",
              intf.name,
              mac,
              ipv4 || "-",
              ipv6 || "-",
            ];
            body.push(row);
          });
        });

        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.text(this.$t("addressing.nodesTitle"), 40, 86);
        doc.setFont("helvetica", "normal");
        autoTable(doc, {
          startY: 90,
          head: [[
            this.$t("addressing.headers.node"),
            this.$t("addressing.headers.type"),
            this.$t("addressing.headers.interface"),
            this.$t("addressing.headers.mac"),
            this.$t("addressing.headers.ipv4"),
            this.$t("addressing.headers.ipv6")
          ]],
          body,
          styles: { fontSize: 8, cellPadding: 3, valign: "top" },
          headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] },
        });

        const afterNodes = doc.lastAutoTable?.finalY ? doc.lastAutoTable.finalY + 24 : 120;
        const linkRows = [];
        const edges = this.edges?.get ? this.edges.get() : [];
        edges.forEach((edge) => {
          linkRows.push([
            edge.from,
            edge.to,
            edge.title || "-",
          ]);
        });

        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.text(this.$t("addressing.linksTitle"), 40, afterNodes - 8);
        doc.setFont("helvetica", "normal");
        autoTable(doc, {
          startY: afterNodes,
          head: [[this.$t("addressing.links.from"), this.$t("addressing.links.to"), this.$t("addressing.links.attributes")]],
          body: linkRows.length ? linkRows : [["-", "-", this.$t("addressing.links.none")]],
          styles: { fontSize: 8, cellPadding: 3, valign: "top" },
          headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] },
        });

        const canvas = this.$refs.graph?.querySelector?.("canvas");
        const imageData = canvas ? canvas.toDataURL("image/png") : null;
        if (imageData) {
          doc.addPage();
          doc.setFont("helvetica", "bold");
          doc.setFontSize(14);
          doc.text(this.$t("addressing.networkGraph"), 40, 40);
          const pageWidth = doc.internal.pageSize.getWidth();
          const pageHeight = doc.internal.pageSize.getHeight();
          const maxWidth = pageWidth - 80;
          const maxHeight = pageHeight - 120;
          const img = new Image();
          img.src = imageData;
          const imgRatio = img.width && img.height ? img.width / img.height : 1.6;
          let imgWidth = maxWidth;
          let imgHeight = imgWidth / imgRatio;
          if (imgHeight > maxHeight) {
            imgHeight = maxHeight;
            imgWidth = imgHeight * imgRatio;
          }
          const x = (pageWidth - imgWidth) / 2;
          const y = 60;
          doc.addImage(imageData, "PNG", x, y, imgWidth, imgHeight, undefined, "FAST");
        }

        doc.save("addressing-plan.pdf");
      } catch (error) {
        console.error("Failed to export addressing plan", error);
        alert(this.$t("errors.exportAddressing"));
      }
    },
    async importTopology(file) {
      await this.resetTopology();
      const data = await requestImportNetwork(file);
      await this.setupNetwork();
      this.network.setData({nodes: this.nodes, edges: this.edges});
      this.network.redraw();
    },
    buildTopologyExportPayload() {
      try {
        const nodes = this.nodes?.get ? this.nodes.get() : [];
        const edges = this.edges?.get ? this.edges.get() : [];
        const pickDefined = (source, keys) => {
          const out = {};
          keys.forEach((key) => {
            if (source?.[key] !== undefined) out[key] = source[key];
          });
          return out;
        };
        const baseNodeFields = (node) => ({
          id: node.id,
          type: node.type,
          name: node.name ?? node.id,
          label: node.label ?? node.name ?? node.id,
          x: node.x,
          y: node.y,
        });
        const normalizeControllerColor = (node) => {
          if (node?.colorCode) return node.colorCode;
          if (typeof node?.color === "string") return node.color;
          if (node?.color && typeof node.color.color === "string") return node.color.color;
          return null;
        };
        const nodesExport = nodes.map((node) => {
            const base = baseNodeFields(node);
            if (node.type === "host") {
              return {
                ...base,
                ...pickDefined(node, ["ip", "mac", "default_route", "default_route_type", "default_route_dev", "default_route_ip"]),
              };
            }
            if (node.type === "router") {
              return {
                ...base,
                ...pickDefined(node, ["ip", "mac"]),
              };
            }
            if (node.type === "controller") {
              return {
                ...base,
                controller_type: node.controller_type ?? (node.remote ? "remote" : "default"),
                remote: node.remote ?? false,
                ip: node.ip ?? null,
                port: node.port ?? null,
                ryu_app: node.ryu_app ?? null,
                color: normalizeControllerColor(node),
              };
            }
            if (node.type === "nat") {
              return {
                ...base,
                ...pickDefined(node, ["ip", "mac"]),
              };
            }
            return {
              ...base,
              dpid: node.dpid,
              ports: node.ports,
              controller: node.controller ?? null,
              switch_type: node.switch_type ?? "ovskernel",
              of_version: node.of_version ?? null,
              ...pickDefined(node, ["stp", "fail_mode"]),
            };
          });
        const edgesExport = edges.map((edge) => ({
          id: edge.id ?? undefined,
          from: edge.from,
          to: edge.to,
          options: edge.options ?? null,
          title: edge.title ?? null,
        }));
        return { nodes: nodesExport, edges: edgesExport };
      } catch (error) {
        console.warn("Failed to build topology export payload", error);
        return { nodes: [], edges: [] };
      }
    },
  }
};
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  position: relative;
  background: var(--theme-app-bg);
  color: var(--theme-app-color);
}

:global(:root) {
  --theme-app-bg: #101010;
  --theme-app-color: #d4d4d4;
  --theme-topbar-bg: #2b2b2b;
  --theme-topbar-color: #d4d4d4;
  --theme-topbar-border: #1f1f1f;
  --theme-menu-hover: #3e3e3e;
  --theme-dropdown-bg: #2d2d2d;
  --theme-dropdown-border: #1f1f1f;
  --theme-health-overlay-bg: rgba(5, 5, 5, 0.92);
  --theme-health-overlay-card-bg: #1e1e1e;
  --theme-health-overlay-card-border: #3a3a3a;
  --theme-health-overlay-card-color: #dcdcdc;
  --theme-statusbar-bg: #1d1d1d;
  --theme-statusbar-color: #d4d4d4;
  --theme-statusbar-border: #2f2f2f;
  --theme-statusbar-muted: #a2a2a2;
  --theme-sidebar-bg: #1e1e1e;
  --theme-sidebar-color: #cccccc;
  --theme-sidebar-border: #333;
  --theme-sidebar-muted: #9b9b9b;
  --theme-sidebar-button-bg: #2d2d2d;
  --theme-sidebar-button-border: #333;
  --theme-sidebar-button-color: #cccccc;
  --theme-sidebar-button-hover: #3e3e3e;
  --theme-sidebar-button-active-bg: #0b2b3b;
  --theme-sidebar-button-active-border: #007acc;
  --theme-sidebar-button-active-color: #e6f2ff;
  --theme-icon-button-hover: #2d2d2d;
  --theme-network-bg: #252526;
  --theme-webshell-bg: #1d1d1d;
  --theme-webshell-color: #ffffff;
  --theme-webshell-border: #444;
  --theme-webshell-header-bg: #2d2d2d;
  --theme-webshell-header-border: #333;
  --theme-webshell-tab-bg: transparent;
  --theme-webshell-tab-color: #cccccc;
  --theme-webshell-tab-hover: #333333;
  --theme-webshell-tab-active-bg: #1e1e1e;
  --theme-webshell-tab-active-color: #ffffff;
  --theme-webshell-icon-color: #cccccc;
  --theme-webshell-tabs-bg: #2d2d2d;
  --theme-webshell-chat-bg: #1f1f1f;
  --theme-webshell-chat-border: #2d2d2d;
  --theme-webshell-chat-input-bg: #121212;
  --theme-webshell-chat-input-border: #333;
  --theme-webshell-chat-input-color: #e5e5e5;
  --theme-webshell-chat-button-bg: #007acc;
  --theme-webshell-chat-button-color: #ffffff;
  --theme-webshell-chat-error: #f87171;
  --theme-node-context-bg: #1f1f1f;
  --theme-node-context-border: #333;
  --theme-node-context-color: #e5e5e5;
  --theme-modal-pre-bg: #0b1220;
  --theme-modal-pre-border: #1f2937;
  --theme-monitoring-toolbar-bg: #1a1a1a;
  --theme-monitoring-toolbar-border: #2a2a2a;
  --theme-monitoring-select-color: #c8c8c8;
  --theme-monitoring-select-bg: #0f0f0f;
  --theme-monitoring-select-border: #333;
  --theme-monitoring-toggle-bg: #111;
  --theme-monitoring-toggle-border: #2a2a2a;
  --theme-monitoring-toggle-color: #ffffff;
  --theme-monitoring-toggle-active-bg: #043f5f;
  --theme-monitoring-toggle-active-border: #07c6ef;
  --theme-monitoring-toggle-active-color: #cff2ff;
  --theme-monitoring-export-bg: #1a1a1a;
  --theme-monitoring-export-border: #2a2a2a;
  --theme-monitoring-clear-bg: #1a1a1a;
  --theme-monitoring-clear-border: #2a2a2a;
  --theme-monitoring-status-color: #9da9b7;
  --theme-monitoring-status-monitoring: #9be2a5;
  --theme-monitoring-status-error: #ff6b6b;
  --theme-chart-card-bg: #111;
  --theme-chart-card-border: #222;
  --theme-chart-label-color: #9da9b7;
  --theme-traffic-toolbar-bg: #1e1e1e;
  --theme-traffic-toolbar-border: #2a2a2a;
  --theme-traffic-status-active: #43b1ff;
  --theme-traffic-status-inactive: #8a8a8a;
  --theme-traffic-select-bg: #1e1e1e;
  --theme-traffic-select-color: #cccccc;
  --theme-traffic-select-border: #333;
  --theme-traffic-button-bg: #1e1e1e;
  --theme-traffic-button-border: #333;
  --theme-traffic-button-color: #cccccc;
  --theme-sniffer-toggle-bg: #2d2d2d;
  --theme-sniffer-toggle-border: #333;
  --theme-sniffer-toggle-color: #cccccc;
  --theme-sniffer-toggle-active-bg: #0b2b3b;
  --theme-sniffer-toggle-active-border: #007acc;
  --theme-sniffer-toggle-active-color: #e6f2ff;
  --theme-traffic-row-color: #cccccc;
  --theme-traffic-row-bg-even: #1f1f1f;
  --theme-traffic-row-header-bg: #262626;
  --theme-traffic-row-header-border: #333;
  --theme-traffic-empty-color: #8a8a8a;
  --theme-input-bg: #1e1e1e;
  --theme-input-border: #333;
}

:global(.theme-light) {
  --theme-app-bg: #f8f8f8;
  --theme-app-color: #000000;
  --theme-topbar-bg: #f8f8f8;
  --theme-topbar-color: #000000;
  --theme-topbar-border: #d0d0d0;
  --theme-menu-hover: #e6e6e6;
  --theme-dropdown-bg: #ffffff;
  --theme-dropdown-border: #d0d0d0;
  --theme-health-overlay-bg: rgba(248, 248, 248, 0.92);
  --theme-health-overlay-card-bg: #ffffff;
  --theme-health-overlay-card-border: #d0d0d0;
  --theme-health-overlay-card-color: #000000;
  --theme-statusbar-bg: #f8f8f8;
  --theme-statusbar-color: #000000;
  --theme-statusbar-border: #d0d0d0;
  --theme-statusbar-muted: #6b6b6b;
  --theme-sidebar-bg: #f8f8f8;
  --theme-sidebar-color: #000000;
  --theme-sidebar-border: #d0d0d0;
  --theme-sidebar-muted: #6b6b6b;
  --theme-sidebar-button-bg: #ffffff;
  --theme-sidebar-button-border: #d0d0d0;
  --theme-sidebar-button-color: #000000;
  --theme-sidebar-button-hover: #e6e6e6;
  --theme-sidebar-button-active-bg: #e6f2ff;
  --theme-sidebar-button-active-border: #007acc;
  --theme-sidebar-button-active-color: #004175;
  --theme-icon-button-hover: #d0d0d0;
  --theme-network-bg: #ffffff;
  --theme-webshell-bg: #f8f8f8;
  --theme-webshell-color: #000000;
  --theme-webshell-border: #d0d0d0;
  --theme-node-context-bg: #ffffff;
  --theme-node-context-border: #d0d0d0;
  --theme-node-context-color: #000000;
  --theme-webshell-header-bg: #f8f8f8;
  --theme-webshell-header-border: #d0d0d0;
  --theme-webshell-tab-bg: transparent;
  --theme-webshell-tab-color: #2b2b2b;
  --theme-webshell-tab-hover: #e6e6e6;
  --theme-webshell-tab-active-bg: #ffffff;
  --theme-webshell-tab-active-color: #000000;
  --theme-webshell-icon-color: #2b2b2b;
  --theme-webshell-tabs-bg: #f8f8f8;
  --theme-webshell-chat-bg: #ffffff;
  --theme-webshell-chat-border: #d0d0d0;
  --theme-webshell-chat-input-bg: #ffffff;
  --theme-webshell-chat-input-border: #d0d0d0;
  --theme-webshell-chat-input-color: #000000;
  --theme-webshell-chat-button-bg: #007acc;
  --theme-webshell-chat-button-color: #ffffff;
  --theme-webshell-chat-error: #f87171;
  --theme-modal-pre-bg: #f5f5f5;
  --theme-modal-pre-border: #d0d0d0;
  --theme-monitoring-toolbar-bg: #f8f8f8;
  --theme-monitoring-toolbar-border: #d0d0d0;
  --theme-monitoring-select-color: #000000;
  --theme-monitoring-select-bg: #ffffff;
  --theme-monitoring-select-border: #d0d0d0;
  --theme-monitoring-toggle-bg: #ffffff;
  --theme-monitoring-toggle-border: #d0d0d0;
  --theme-monitoring-toggle-color: #000000;
  --theme-monitoring-toggle-active-bg: #e6f2ff;
  --theme-monitoring-toggle-active-border: #007acc;
  --theme-monitoring-toggle-active-color: #0b2b3b;
  --theme-monitoring-export-bg: #ffffff;
  --theme-monitoring-export-border: #d0d0d0;
  --theme-monitoring-clear-bg: #ffffff;
  --theme-monitoring-clear-border: #d0d0d0;
  --theme-monitoring-status-color: #6b6b6b;
  --theme-monitoring-status-monitoring: #2f7d46;
  --theme-monitoring-status-error: #c62828;
  --theme-chart-card-bg: #ffffff;
  --theme-chart-card-border: #d0d0d0;
  --theme-chart-label-color: #6b6b6b;
  --theme-traffic-toolbar-bg: #f8f8f8;
  --theme-traffic-toolbar-border: #d0d0d0;
  --theme-traffic-status-active: #0b6fa5;
  --theme-traffic-status-inactive: #6b6b6b;
  --theme-traffic-select-bg: #ffffff;
  --theme-traffic-select-color: #2b2b2b;
  --theme-traffic-select-border: #d0d0d0;
  --theme-traffic-button-bg: #ffffff;
  --theme-traffic-button-border: #d0d0d0;
  --theme-traffic-button-color: #2b2b2b;
  --theme-sniffer-toggle-bg: #f8f8f8;
  --theme-sniffer-toggle-border: #d0d0d0;
  --theme-sniffer-toggle-color: #000000;
  --theme-sniffer-toggle-active-bg: #e6f2ff;
  --theme-sniffer-toggle-active-border: #007acc;
  --theme-sniffer-toggle-active-color: #0b2b3b;
  --theme-traffic-row-color: #2b2b2b;
  --theme-traffic-row-bg-even: #f5f5f5;
  --theme-traffic-row-header-bg: #efefef;
  --theme-traffic-row-header-border: #d0d0d0;
  --theme-traffic-empty-color: #6b6b6b;
  --theme-input-bg: #ffffff;
  --theme-input-border: #d0d0d0;
}

.topbar {
  height: 32px;
  background: var(--theme-topbar-bg);
  color: var(--theme-topbar-color);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 12px;
  border-bottom: 1px solid var(--theme-topbar-border);
  position: relative;
  z-index: 6;
  font-size: 0.85rem;
}

.topbar-title {
  font-weight: 600;
  letter-spacing: 0.2px;
  margin-right: 8px;
}

.menu-bar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.menu-item-wrapper {
  position: relative;
}

.menu-item {
  background: transparent;
  border: none;
  color: inherit;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.menu-item:hover,
.menu-item.open {
  background: var(--theme-menu-hover);
}

.menu-item:disabled {
  color: #7a7a7a;
  cursor: default;
}

.menu-dropdown {
  position: absolute;
  top: 28px;
  left: 0;
  background: var(--theme-dropdown-bg);
  border: 1px solid var(--theme-dropdown-border);
  border-radius: 6px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 240px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.35);
}

.menu-action {
  background: transparent;
  border: none;
  color: var(--theme-app-color);
  padding: 6px 10px;
  text-align: left;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.menu-action:hover {
  background: var(--theme-menu-hover);
}

.menu-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--theme-app-color);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.82rem;
  cursor: pointer;
}

.menu-checkbox:hover {
  background: var(--theme-menu-hover);
}

.menu-checkbox input {
  accent-color: #007acc;
}

.health-overlay {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 28px;
  background: var(--theme-health-overlay-bg);
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.health-overlay__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: var(--theme-health-overlay-card-bg);
  border: 1px solid var(--theme-health-overlay-card-border);
  border-radius: 12px;
  padding: 20px 28px;
  max-width: 360px;
  text-align: center;
  color: var(--theme-health-overlay-card-color);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
}

.health-overlay__retry {
  margin-top: 4px;
  width: auto;
}

.menu-separator {
  height: 1px;
  margin: 4px 0;
  background: var(--theme-topbar-border);
}

.menu-file-input {
  display: none;
}

.status-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 28px;
  background: var(--theme-statusbar-bg);
  border-top: 1px solid var(--theme-statusbar-border);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 16px;
  z-index: 7;
  font-size: 0.8rem;
  color: var(--theme-statusbar-color);
}

.status-bar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background-color: #9b9b9b;
}

.status-dot--started {
  background-color: #61efb5;
}

.status-dot--stopped {
  background-color: #9b9b9b;
}

.status-bar__text {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  line-height: 1;
  font-size: 0.7rem;
}

.status-bar__primary {
  font-weight: 600;
}

.status-bar__version {
  color: var(--theme-statusbar-muted);
}

.status-bar__counts {
  color: var(--theme-statusbar-color);
  font-weight: 500;
}

.status-bar__network {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--theme-statusbar-color);
}

.network-state-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background-color: #9b9b9b;
}

.network-state--started {
  background-color: #61efb5;
}

.network-state--stopped {
  background-color: #f06666;
}

.network-state--pending {
  background-color: #f5d76a;
}

.layout {
  display: flex;
  height: calc(100vh - 32px);
  overflow: hidden;
  width: 100%;
  --sidebar-width: 220px;
}

.layout.sidebar-collapsed {
  --sidebar-width: 64px;
}

.side-wrapper {
  padding: 8px;
  display: flex;
  flex-shrink: 0;
  width: calc(var(--sidebar-width) + 16px);
  min-width: calc(var(--sidebar-width) + 16px);
  max-width: calc(var(--sidebar-width) + 16px);
}

  .main-content {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    min-width: 0;
    position: relative;
    z-index: 0;
    width: calc(100% - var(--sidebar-width));
    padding-bottom: 28px;
    box-sizing: border-box;
  }

.graph-wrapper {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
}

.side-container {
  position: relative;
  /* min-width: 10vw; */
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  max-width: var(--sidebar-width);
  display: flex;
  flex-direction: row;
  justify-content: stretch;
  flex-shrink: 0;
  z-index: 1;
}

.network-graph {
  flex: 1 1 auto;
  min-height: 0;
  background: var(--theme-network-bg);
  overflow: hidden;
  position: absolute;
  inset: 0;
}

.selection-rect {
  position: absolute;
  border: 1px solid rgba(0, 122, 204, 0.9);
  pointer-events: none;
  z-index: 5;
}

.webshell {
  flex: 0 0 auto;
  height: auto;
  background: var(--theme-webshell-bg);
  color: var(--theme-webshell-color);
  border-top: 2px solid var(--theme-webshell-border);
  overflow: hidden;
  position: relative;
  z-index: 1;
  margin-top: 0;
}

.webshell :deep(.webshell-container.minimized) {
  transform: translateY(-24px);
}

.node-context-menu {
  position: fixed;
  z-index: 10;
  background: var(--theme-node-context-bg);
  border: 1px solid var(--theme-node-context-border);
  border-radius: 6px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

.node-context-item {
  background: transparent;
  border: none;
  color: var(--theme-node-context-color);
  padding: 6px 8px;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.85rem;
}

.node-context-item:hover {
  background: var(--theme-menu-hover);
}

.modal-pre {
  background: var(--theme-modal-pre-bg);
  border: 1px solid var(--theme-modal-pre-border);
  color: var(--theme-app-color);
  padding: 12px;
  border-radius: 10px;
  font-size: 12px;
  white-space: pre-wrap;
}

.modal-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.about-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  align-items: center;
}

.about-logo {
  width: 200px;
  height: auto;
  justify-self: center;
}

.about-details p {
  margin: 4px 0;
  font-size: 13px;
}

.about-link {
  color: #60a5fa;
  text-decoration: underline;
  word-break: break-all;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.settings-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--theme-app-color);
}

.settings-toggle input {
  width: 16px;
  height: 16px;
}
</style>
