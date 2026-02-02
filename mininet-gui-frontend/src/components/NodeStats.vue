<script>
import { addFlow, deleteFlowById, getNodeStats, listFlows, updateHost } from "@/core/api";

export default {
  props: ["stats"],
  emits: ["hostUpdated", "editController"],
  data() {
    return {
      activeTab: "details",
      tabs: [
        { key: "details", labelKey: "node.tabs.details" }
      ],
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
      return Object.entries(matchFields).map(([key, value]) => `${key}: ${value}`).join(', ');
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
  },
  created() {
    if (this.stats?.type === "sw" || this.stats?.type === "switch") {
      this.tabs.push({ key: "flows", labelKey: "node.tabs.flowTable" });
    }
    if (this.stats?.type === "host") {
      this.tabs.push({ key: "arp", labelKey: "node.tabs.arpTable" });
    }
  }
};
</script>

<template>
  <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="{ active: activeTab === tab.key }" @click="setTab(tab.key)">
      {{ tab.labelKey ? $t(tab.labelKey) : tab.label }}
      </button>
  </div>

  <div class="tab-content">
    <div v-if="isDetailsTab">
      <div v-if="isController" class="host-edit">
        <button @click="triggerControllerEdit">{{ $t("node.editController") }}</button>
      </div>
      <div v-if="isHost" class="host-edit">
        <button v-if="!isEditingHost" @click="startHostEdit">{{ $t("actions.edit") }}</button>
        <div v-else class="host-edit-actions">
          <button :disabled="hostEditBusy" @click="saveHostEdit">{{ $t("actions.save") }}</button>
          <button :disabled="hostEditBusy" @click="cancelHostEdit">{{ $t("actions.cancel") }}</button>
        </div>
        <p v-if="hostEditError" class="flow-error">{{ hostEditError }}</p>
      </div>
      <div v-if="isHost && isEditingHost" class="host-edit-fields">
        <label>
          {{ $t("node.hostIp") }}
          <input v-model="hostEdit.ip" type="text" class="host-edit-input" />
        </label>
        <label>
          {{ $t("node.defaultRouteType") }}
          <select v-model="hostEdit.routeType" class="host-edit-select">
            <option value="dev">{{ $t("node.routeDevice") }}</option>
            <option value="ip">{{ $t("node.routeGateway") }}</option>
          </select>
        </label>
        <label v-if="hostEdit.routeType === 'dev'">
          {{ $t("node.interface") }}
          <select v-model="hostEdit.routeDev" class="host-edit-select">
            <option value="">{{ $t("node.selectInterface") }}</option>
            <option v-for="intf in (localStats?.interfaces || [])" :key="intf" :value="intf">
              {{ intf }}
            </option>
          </select>
        </label>
        <label v-if="hostEdit.routeType === 'ip'">
          {{ $t("node.gatewayIp") }}
          <input v-model="hostEdit.routeIp" type="text" class="host-edit-input" placeholder="10.0.0.254" />
        </label>
      </div>
      <ul class="stats-list">
        <li v-for="(value, key) in filteredDetails" :key="key">
          <strong>{{ key }}:</strong>
          <span>{{ value }}</span>
        </li>
        <li v-if="isHost && !isEditingHost">
          <strong>{{ $t("node.defaultRoute") }}:</strong> {{ localStats?.default_route || "" }}
        </li>
      </ul>
    </div>

    <div v-if="isFlowTableTab">
      <div class="flow-actions flow-actions-top">
        <button :disabled="flowBusy" @click="showFlowForm = !showFlowForm">
          {{ showFlowForm ? $t("node.hideFlowForm") : $t("node.addFlow") }}
        </button>
        <button :disabled="flowBusy" @click="refreshFlows">{{ $t("actions.refresh") }}</button>
      </div>
      <div v-if="showFlowForm" class="flow-editor">
        <div class="flow-fields">
          <label>
            {{ $t("node.flow.match") }}
            <input v-model="flowForm.match" type="text" placeholder="ip,nw_src=10.0.0.1" />
          </label>
          <label>
            {{ $t("node.flow.actions") }}
            <input v-model="flowForm.actions" type="text" placeholder="output:2" />
          </label>
          <label>
            {{ $t("node.flow.priority") }}
            <input v-model="flowForm.priority" type="number" min="0" placeholder="100" />
          </label>
          <label>
            {{ $t("node.flow.table") }}
            <input v-model="flowForm.table" type="number" min="0" placeholder="0" />
          </label>
          <label>
            {{ $t("node.flow.idleTimeout") }}
            <input v-model="flowForm.idle_timeout" type="number" min="0" placeholder="30" />
          </label>
          <label>
            {{ $t("node.flow.hardTimeout") }}
            <input v-model="flowForm.hard_timeout" type="number" min="0" placeholder="0" />
          </label>
          <label>
            {{ $t("node.flow.cookie") }}
            <input v-model="flowForm.cookie" type="text" placeholder="0x1" />
          </label>
          <label>
            {{ $t("node.flow.openflow") }}
            <select v-model="flowForm.of_version">
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
        <div class="flow-actions">
          <button :disabled="flowBusy" @click="submitFlow">{{ $t("node.addFlow") }}</button>
        </div>
      </div>
      <p v-if="flowError" class="flow-error">{{ flowError }}</p>
      <div class="flow-table">
        <table>
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
                <button class="flow-delete" :disabled="flowBusy" @click="deleteFlow(flow, index + 1)">
                  <span class="material-symbols-outlined" aria-hidden="true">delete</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="flow-dump">
        <h4>{{ $t("node.flow.rawDump") }}</h4>
        <pre>{{ flowDump }}</pre>
      </div>
    </div>

    <div v-if="isArpTableTab">
      <div class="arp-table">
        <table>
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
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.tabs button {
  padding: 8px 12px;
  border: 1px solid #ccc;
  background: #f8f8f8;
  cursor: pointer;
  transition: background 0.2s ease-in-out;
}

.tabs button:hover {
  background: #e8e8e8;
}

.tabs button.active {
  background: #42b983;
  color: white;
  font-weight: bold;
}

.host-edit {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.host-edit-actions {
  display: flex;
  gap: 8px;
}

.host-edit-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.host-edit-fields label {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #b8b8b8;
  gap: 4px;
}

.host-edit-input {
  padding: 6px 8px;
  border: 1px solid #333;
  border-radius: 6px;
  font-size: 12px;
  background: #1e1e1e;
  color: #e6e6e6;
  min-width: 160px;
}

.host-edit-input::placeholder {
  color: #777;
}

.host-edit-select {
  padding: 6px 8px;
  border: 1px solid #333;
  border-radius: 6px;
  font-size: 12px;
  background: #1e1e1e;
  color: #e6e6e6;
}

.host-edit-select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.host-edit-select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.tab-content {
  width: 80vw;
  max-height: 400px;
  overflow-y: auto;
  text-align: left;
}

.flow-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.flow-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.flow-fields label {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #555;
  gap: 4px;
}

.flow-fields input,
.flow-fields select {
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 12px;
}

.flow-fields select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.flow-fields select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.flow-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.flow-actions button,
.flow-table button {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #f2f2f2;
  cursor: pointer;
}

.flow-actions button:hover,
.flow-table button:hover {
  background: #e6e6e6;
}

.flow-actions button:disabled,
.flow-table button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.flow-actions-top {
  margin-bottom: 12px;
}

.flow-delete {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #f5b5b5;
  background: #ffecec;
  color: #c62828;
  border-radius: 6px;
}

.flow-delete:hover {
  background: #ffd9d9;
}

.flow-error {
  color: #b00020;
  font-size: 12px;
}

.flow-dump {
  margin-top: 12px;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fcfcfc;
}

.flow-dump pre {
  white-space: pre-wrap;
  font-size: 12px;
}

.stats-list, .flow-table, .arp-table {
  list-style: none;
  padding: 0;
}

.flow-table table {
  width: 100%;
  border-collapse: collapse;
}

.flow-table th, .flow-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.flow-table {
  max-width: 100%;
  overflow: auto;
}

.arp-table table {
  width: 100%;
  border-collapse: collapse;
}

.arp-table th, .arp-table td {
  border: 1px solid #ddd;
  padding: 8px;
}

.arp-table th {
  background: #f1f1f1;
  text-align: left;
}
</style>
