<script>
import { addFlow, deleteFlowById, getNodeStats, listFlows, updateHost, updateSwitchOpenflowVersion } from "@/core/api";

export default {
  props: ["stats"],
  emits: ["hostUpdated", "editController"],
  data() {
    return {
      activeTab: "details",
      tabs: [{ key: "details", labelKey: "node.tabs.details" }],
      localStats: this.stats,
      isEditingHost: false,
      hostEdit: {
        ip: "",
        defaultRoute: "",
        routeType: "dev",
        routeDev: "",
        routeIp: "",
      },
      hostEditBusy: false,
      hostEditError: "",
      flowDump: "",
      flowBusy: false,
      flowError: "",
      switchOpenflow: "",
      switchOpenflowBusy: false,
      switchOpenflowError: "",
      switchOpenflowSuccess: false,
      showFlowForm: false,
      flowForm: {
        match: "",
        actions: "",
        priority: "",
        table: "",
        idle_timeout: "",
        hard_timeout: "",
        cookie: "",
        of_version: "",
      },
    };
  },
  computed: {
    isDetailsTab() {
      return this.activeTab === "details";
    },
    isController() {
      return this.localStats?.type === "controller";
    },
    isFlowTableTab() {
      return this.activeTab === "flows";
    },
    isArpTableTab() {
      return this.activeTab === "arp";
    },
    filteredDetails() {
      const { flow_table, arp_table, ...details } = this.localStats || {};
      if (this.isHost) {
        const { default_route, interfaces, ...rest } = details;
        return rest;
      }
      return details;
    },
    isSwitch() {
      return this.localStats?.type === "sw" || this.localStats?.type === "switch";
    },
    isHost() {
      return this.localStats?.type === "host";
    },
    canSetOpenflow() {
      const type = (this.localStats?.switch_type || "").toLowerCase();
      return this.isSwitch && ["ovs", "ovskernel", "ovsbridge"].includes(type);
    },
  },
  watch: {
    stats: {
      immediate: true,
      handler(value) {
        this.localStats = value;
        if (value?.type === "host") {
          this.hostEdit.ip = value?.ip || "";
          this.hostEdit.defaultRoute = value?.default_route || "";
          this.applyDefaultRouteToForm();
          this.isEditingHost = false;
          this.hostEditError = "";
        }
        if (value?.type === "sw" || value?.type === "switch") {
          this.refreshFlows();
          this.switchOpenflow = value?.of_version || "";
          this.switchOpenflowError = "";
          this.switchOpenflowSuccess = false;
        }
      },
    },
  },
  methods: {
    triggerControllerEdit() {
      if (!this.localStats?.id) return;
      this.$emit("editController", this.localStats.id);
    },
    setTab(tabKey) {
      this.activeTab = tabKey;
    },
    formatMatchFields(matchFields) {
      return Object.entries(matchFields || {})
        .map(([key, value]) => `${key}: ${value}`)
        .join(", ");
    },
    startHostEdit() {
      if (!this.isHost) return;
      this.isEditingHost = true;
      this.hostEditError = "";
      this.hostEdit.ip = this.localStats?.ip || "";
      this.hostEdit.defaultRoute = this.localStats?.default_route || "";
      this.applyDefaultRouteToForm();
    },
    cancelHostEdit() {
      this.isEditingHost = false;
      this.hostEditError = "";
      this.hostEdit.ip = this.localStats?.ip || "";
      this.hostEdit.defaultRoute = this.localStats?.default_route || "";
      this.applyDefaultRouteToForm();
    },
    async saveHostEdit() {
      if (!this.isHost || !this.localStats?.id) return;
      this.hostEditBusy = true;
      this.hostEditError = "";
      try {
        const payload = {
          ip: this.hostEdit.ip,
          default_route_type: this.hostEdit.routeType,
          default_route_dev: this.hostEdit.routeType === "dev" ? this.hostEdit.routeDev : null,
          default_route_ip: this.hostEdit.routeType === "ip" ? this.hostEdit.routeIp : null,
        };
        const response = await updateHost(this.localStats.id, payload);
        if (!response?.host) {
          this.hostEditError = this.$t("node.errors.updateHost");
          return;
        }
        const refreshed = await getNodeStats(this.localStats.id);
        if (refreshed) {
          this.localStats = refreshed;
          this.$emit("hostUpdated", refreshed);
        }
        this.isEditingHost = false;
      } catch (error) {
        this.hostEditError = this.$t("node.errors.updateHost");
      } finally {
        this.hostEditBusy = false;
      }
    },
    applyDefaultRouteToForm() {
      const route = (this.localStats?.default_route || "").trim();
      this.hostEdit.routeType = "dev";
      this.hostEdit.routeDev = "";
      this.hostEdit.routeIp = "";
      if (!route) return;
      const viaMatch = route.match(/\bvia\s+([0-9.]+)/);
      const devMatch = route.match(/\bdev\s+(\S+)/);
      if (viaMatch && !devMatch) {
        this.hostEdit.routeType = "ip";
        this.hostEdit.routeIp = viaMatch[1];
        return;
      }
      if (devMatch) {
        this.hostEdit.routeType = "dev";
        this.hostEdit.routeDev = devMatch[1];
        if (viaMatch) {
          this.hostEdit.routeIp = viaMatch[1];
        }
      }
    },
    async refreshFlows() {
      if (!this.localStats?.id || !this.isSwitch) return;
      this.flowBusy = true;
      this.flowError = "";
      try {
        const response = await listFlows(this.localStats.id);
        this.flowDump = response?.flows || "";
        const refreshed = await getNodeStats(this.localStats.id);
        if (refreshed) {
          this.localStats = refreshed;
        }
      } catch (error) {
        this.flowError = this.$t("node.errors.refreshFlows");
      } finally {
        this.flowBusy = false;
      }
    },
    async submitFlow() {
      if (!this.localStats?.id || !this.isSwitch) return;
      this.flowBusy = true;
      this.flowError = "";
      try {
        if (!this.flowForm.actions) {
          this.flowError = this.$t("node.errors.actionsRequired");
          return;
        }
        const payload = {
          switch: this.localStats.id,
          actions: this.flowForm.actions,
          match: this.flowForm.match || undefined,
          priority: this.flowForm.priority ? Number(this.flowForm.priority) : undefined,
          table: this.flowForm.table ? Number(this.flowForm.table) : undefined,
          idle_timeout: this.flowForm.idle_timeout ? Number(this.flowForm.idle_timeout) : undefined,
          hard_timeout: this.flowForm.hard_timeout ? Number(this.flowForm.hard_timeout) : undefined,
          cookie: this.flowForm.cookie || undefined,
          of_version: this.flowForm.of_version || undefined,
        };
        await addFlow(payload);
        await this.refreshFlows();
        this.showFlowForm = false;
      } catch (error) {
        this.flowError = this.$t("node.errors.addFlow");
      } finally {
        this.flowBusy = false;
      }
    },
    async deleteFlow(flow, flowId) {
      if (!this.localStats?.id || !this.isSwitch) return;
      this.flowBusy = true;
      this.flowError = "";
      try {
        await deleteFlowById(this.localStats.id, flowId);
        await this.refreshFlows();
      } catch (error) {
        this.flowError = this.$t("node.errors.deleteFlow");
      } finally {
        this.flowBusy = false;
      }
    },
    async saveSwitchOpenflow() {
      if (!this.isSwitch || !this.localStats?.id) return;
      this.switchOpenflowBusy = true;
      this.switchOpenflowError = "";
      this.switchOpenflowSuccess = false;
      try {
        const payload = {
          of_version: this.switchOpenflow || null,
        };
        const updated = await updateSwitchOpenflowVersion(this.localStats.id, payload);
        if (!updated) {
          this.switchOpenflowError = this.$t("node.errors.updateSwitch");
          return;
        }
        this.localStats = { ...this.localStats, of_version: updated.of_version ?? null };
        this.switchOpenflowSuccess = true;
      } catch (error) {
        this.switchOpenflowError = this.$t("node.errors.updateSwitch");
      } finally {
        this.switchOpenflowBusy = false;
        if (this.switchOpenflowSuccess) {
          setTimeout(() => {
            this.switchOpenflowSuccess = false;
          }, 1500);
        }
      }
    },
  },
  created() {
    if (this.stats?.type === "sw" || this.stats?.type === "switch") {
      this.tabs.push({ key: "flows", labelKey: "node.tabs.flowTable" });
    }
    if (this.stats?.type === "host") {
      this.tabs.push({ key: "arp", labelKey: "node.tabs.arpTable" });
    }
  },
};
</script>

<template>
  <div class="modal-ui node-stats">
    <div class="modal-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="modal-tab"
        :class="{ 'is-active': activeTab === tab.key }"
        @click="setTab(tab.key)"
      >
        {{ tab.labelKey ? $t(tab.labelKey) : tab.label }}
      </button>
    </div>

    <div class="tab-content modal-tab-panels">
      <div class="modal-ui tab-panel" :class="{ 'is-hidden': !isDetailsTab }">
        <div v-if="isController" class="modal-section">
          <div class="modal-section__header">
            <div class="modal-section__title">{{ $t("node.controllerSection") }}</div>
            <button class="modal-button" @click="triggerControllerEdit">
              {{ $t("node.editController") }}
            </button>
          </div>
        </div>

        <div v-if="isSwitch" class="modal-section">
          <div class="modal-section__header">
            <div class="modal-section__title">{{ $t("node.switchConfigSection") }}</div>
            <span class="modal-muted">{{ $t("node.openflowVersion") }}</span>
          </div>
          <div class="modal-form-grid">
            <label class="modal-field">
              {{ $t("node.openflowVersion") }}
              <select v-model="switchOpenflow" class="modal-select" :disabled="!canSetOpenflow">
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
          <div class="modal-actions">
            <button class="modal-button modal-button--primary" :disabled="switchOpenflowBusy || !canSetOpenflow" @click="saveSwitchOpenflow">
              {{ $t("actions.save") }}
            </button>
            <span v-if="switchOpenflowSuccess" class="modal-success">{{ $t("actions.saved") }}</span>
            <span v-if="switchOpenflowError" class="modal-error">{{ switchOpenflowError }}</span>
            <span v-if="!canSetOpenflow" class="modal-error">{{ $t("node.openflowUnsupported") }}</span>
          </div>
        </div>

        <div v-if="isHost" class="modal-section">
          <div class="modal-section__header">
            <div class="modal-section__title">{{ $t("node.hostConfigSection") }}</div>
            <div class="modal-actions">
              <button v-if="!isEditingHost" class="modal-button" @click="startHostEdit">
                {{ $t("actions.edit") }}
              </button>
              <div v-else class="modal-actions">
                <button class="modal-button modal-button--primary" :disabled="hostEditBusy" @click="saveHostEdit">
                  {{ $t("actions.save") }}
                </button>
                <button class="modal-button" :disabled="hostEditBusy" @click="cancelHostEdit">
                  {{ $t("actions.cancel") }}
                </button>
              </div>
            </div>
          </div>
          <p v-if="hostEditError" class="modal-error">{{ hostEditError }}</p>
          <div v-if="isEditingHost" class="modal-form-grid">
            <label class="modal-field">
              {{ $t("node.hostIp") }}
              <input v-model="hostEdit.ip" type="text" class="modal-input" />
            </label>
            <label class="modal-field">
              {{ $t("node.defaultRouteType") }}
              <select v-model="hostEdit.routeType" class="modal-select">
                <option value="dev">{{ $t("node.routeDevice") }}</option>
                <option value="ip">{{ $t("node.routeGateway") }}</option>
              </select>
            </label>
            <label v-if="hostEdit.routeType === 'dev'" class="modal-field">
              {{ $t("node.interface") }}
              <select v-model="hostEdit.routeDev" class="modal-select">
                <option value="">{{ $t("node.selectInterface") }}</option>
                <option v-for="intf in (localStats?.interfaces || [])" :key="intf" :value="intf">
                  {{ intf }}
                </option>
              </select>
            </label>
            <label v-if="hostEdit.routeType === 'ip'" class="modal-field">
              {{ $t("node.gatewayIp") }}
              <input v-model="hostEdit.routeIp" type="text" class="modal-input" placeholder="10.0.0.254" />
            </label>
          </div>
        </div>

        <div class="modal-section">
          <div class="modal-section__header">
            <div class="modal-section__title">{{ $t("node.detailsSection") }}</div>
          </div>
          <div class="modal-table__wrapper">
            <table class="modal-table modal-table--compact">
              <tbody>
                <tr v-for="(value, key) in filteredDetails" :key="key">
                  <th scope="row">{{ key }}</th>
                  <td>{{ value }}</td>
                </tr>
                <tr v-if="isHost && !isEditingHost">
                  <th scope="row">{{ $t("node.defaultRoute") }}</th>
                  <td>{{ localStats?.default_route || "" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="modal-ui tab-panel" :class="{ 'is-hidden': !isFlowTableTab }">
        <div class="modal-section">
          <div class="modal-section__header">
            <div class="modal-section__title">{{ $t("node.flowTableSection") }}</div>
            <div class="modal-actions">
              <button class="modal-button" :disabled="flowBusy" @click="showFlowForm = !showFlowForm">
                {{ showFlowForm ? $t("node.hideFlowForm") : $t("node.addFlow") }}
              </button>
              <button class="modal-button" :disabled="flowBusy" @click="refreshFlows">{{ $t("actions.refresh") }}</button>
            </div>
          </div>
          <div v-if="showFlowForm" class="flow-editor">
            <div class="modal-form-grid">
              <label class="modal-field">
                {{ $t("node.flow.match") }}
                <input v-model="flowForm.match" type="text" class="modal-input" placeholder="ip,nw_src=10.0.0.1" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.actions") }}
                <input v-model="flowForm.actions" type="text" class="modal-input" placeholder="output:2" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.priority") }}
                <input v-model="flowForm.priority" type="number" min="0" class="modal-input" placeholder="100" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.table") }}
                <input v-model="flowForm.table" type="number" min="0" class="modal-input" placeholder="0" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.idleTimeout") }}
                <input v-model="flowForm.idle_timeout" type="number" min="0" class="modal-input" placeholder="30" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.hardTimeout") }}
                <input v-model="flowForm.hard_timeout" type="number" min="0" class="modal-input" placeholder="0" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.cookie") }}
                <input v-model="flowForm.cookie" type="text" class="modal-input" placeholder="0x1" />
              </label>
              <label class="modal-field">
                {{ $t("node.flow.openflow") }}
                <select v-model="flowForm.of_version" class="modal-select">
                  <option value="">{{ $t("node.flow.auto") }}</option>
                  <option value="OpenFlow10">OpenFlow10</option>
                  <option value="OpenFlow11">OpenFlow11</option>
                  <option value="OpenFlow12">OpenFlow12</option>
                  <option value="OpenFlow13">OpenFlow13</option>
                  <option value="OpenFlow14">OpenFlow14</option>
                  <option value="OpenFlow15">OpenFlow15</option>
                </select>
              </label>
            </div>
            <div class="modal-actions">
              <button class="modal-button modal-button--primary" :disabled="flowBusy" @click="submitFlow">{{ $t("node.addFlow") }}</button>
            </div>
          </div>
          <p v-if="flowError" class="modal-error">{{ flowError }}</p>
          <div class="modal-table__wrapper">
            <table class="modal-table">
              <thead>
                <tr>
                  <th>{{ $t("node.flow.headers.flowId") }}</th>
                  <th>{{ $t("node.flow.headers.cookie") }}</th>
                  <th>{{ $t("node.flow.headers.duration") }}</th>
                  <th>{{ $t("node.flow.headers.table") }}</th>
                  <th>{{ $t("node.flow.headers.packets") }}</th>
                  <th>{{ $t("node.flow.headers.bytes") }}</th>
                  <th>{{ $t("node.flow.headers.idleTimeout") }}</th>
                  <th>{{ $t("node.flow.headers.priority") }}</th>
                  <th>{{ $t("node.flow.headers.matchFields") }}</th>
                  <th>{{ $t("node.flow.headers.actions") }}</th>
                  <th>{{ $t("actions.delete") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(flow, index) in (localStats?.flow_table || [])" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ flow.cookie }}</td>
                  <td>{{ flow.duration }}</td>
                  <td>{{ flow.table }}</td>
                  <td>{{ flow.n_packets }}</td>
                  <td>{{ flow.n_bytes }}</td>
                  <td>{{ flow.idle_timeout }}</td>
                  <td>{{ flow.priority }}</td>
                  <td>{{ formatMatchFields(flow.match_fields) }}</td>
                  <td>{{ flow.actions }}</td>
                  <td>
                    <button class="modal-button modal-button--danger flow-delete" :disabled="flowBusy" @click="deleteFlow(flow, index + 1)">
                      <span class="material-symbols-outlined" aria-hidden="true">delete</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flow-dump">
            <div class="modal-section__title">{{ $t("node.flow.rawDump") }}</div>
            <pre class="modal-pre">{{ flowDump }}</pre>
          </div>
        </div>
      </div>

      <div class="modal-ui tab-panel" :class="{ 'is-hidden': !isArpTableTab }">
        <div class="modal-section">
          <div class="modal-section__header">
            <div class="modal-section__title">{{ $t("node.arpTableSection") }}</div>
          </div>
          <div class="modal-table__wrapper">
            <table class="modal-table">
              <thead>
                <tr>
                  <th>{{ $t("node.arp.ip") }}</th>
                  <th>{{ $t("node.arp.mac") }}</th>
                  <th>{{ $t("node.arp.interface") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in (localStats?.arp_table || [])" :key="entry.ip">
                  <td>{{ entry.ip }}</td>
                  <td>{{ entry.mac }}</td>
                  <td>{{ entry.interface }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-stats {
  min-width: 520px;
}

.tab-content {
  width: 80vw;
  max-height: 420px;
  overflow-y: auto;
  text-align: left;
}

.flow-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
  margin-bottom: 12px;
}

.flow-delete {
  padding: 4px 8px;
}

.flow-dump {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
