<script>
import { addFlow, deleteFlowById, getNodeStats, listFlows } from "@/core/api";

export default {
  props: ["stats"],
  data() {
    return {
      activeTab: "details",
      tabs: [
        { key: "details", label: "Details" }
      ],
      localStats: this.stats,
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
    isFlowTableTab() {
      return this.activeTab === "flows";
    },
    isArpTableTab() {
      return this.activeTab === "arp";
    },
    filteredDetails() {
      const { flow_table, arp_table, ...details } = this.localStats || {};
      return details;
    },
    isSwitch() {
      return this.localStats?.type === "sw" || this.localStats?.type === "switch";
    },
  },
  watch: {
    stats: {
      immediate: true,
      handler(value) {
        this.localStats = value;
        if (value?.type === "sw" || value?.type === "switch") {
          this.refreshFlows();
        }
      },
    },
  },
  methods: {
    setTab(tabKey) {
      this.activeTab = tabKey;
    },
    formatMatchFields(matchFields) {
      return Object.entries(matchFields).map(([key, value]) => `${key}: ${value}`).join(', ');
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
        this.flowError = "Failed to refresh flows.";
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
          this.flowError = "Actions is required.";
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
        this.flowError = "Failed to add flow.";
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
        this.flowError = "Failed to delete flow.";
      } finally {
        this.flowBusy = false;
      }
    },
  },
  created() {
    if (this.stats?.type === "sw" || this.stats?.type === "switch") {
      this.tabs.push({ key: "flows", label: "Flow Table" });
    }
    if (this.stats?.type === "host") {
      this.tabs.push({ key: "arp", label: "ARP Table" });
    }
  }
};
</script>

<template>
  <div class="tabs">
    <button v-for="tab in tabs" :key="tab.key" :class="{ active: activeTab === tab.key }" @click="setTab(tab.key)">
      {{ tab.label }}
    </button>
  </div>

  <div class="tab-content">
    <div v-if="isDetailsTab">
      <ul class="stats-list">
        <li v-for="(value, key) in filteredDetails" :key="key">
          <strong>{{ key }}:</strong> {{ value }}
        </li>
      </ul>
    </div>

    <div v-if="isFlowTableTab">
      <div class="flow-actions flow-actions-top">
        <button :disabled="flowBusy" @click="showFlowForm = !showFlowForm">
          {{ showFlowForm ? "Hide Flow Form" : "Add Flow" }}
        </button>
        <button :disabled="flowBusy" @click="refreshFlows">Refresh</button>
      </div>
      <div v-if="showFlowForm" class="flow-editor">
        <div class="flow-fields">
          <label>
            Match
            <input v-model="flowForm.match" type="text" placeholder="ip,nw_src=10.0.0.1" />
          </label>
          <label>
            Actions
            <input v-model="flowForm.actions" type="text" placeholder="output:2" />
          </label>
          <label>
            Priority
            <input v-model="flowForm.priority" type="number" min="0" placeholder="100" />
          </label>
          <label>
            Table
            <input v-model="flowForm.table" type="number" min="0" placeholder="0" />
          </label>
          <label>
            Idle Timeout
            <input v-model="flowForm.idle_timeout" type="number" min="0" placeholder="30" />
          </label>
          <label>
            Hard Timeout
            <input v-model="flowForm.hard_timeout" type="number" min="0" placeholder="0" />
          </label>
          <label>
            Cookie
            <input v-model="flowForm.cookie" type="text" placeholder="0x1" />
          </label>
          <label>
            OpenFlow
            <select v-model="flowForm.of_version">
              <option value="">auto</option>
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
          <button :disabled="flowBusy" @click="submitFlow">Add Flow</button>
        </div>
      </div>
      <p v-if="flowError" class="flow-error">{{ flowError }}</p>
      <div class="flow-table">
        <table>
          <thead>
            <tr>
              <th>Flow ID</th>
              <th>Cookie</th>
              <th>Duration</th>
              <th>Table</th>
              <th>Packets</th>
              <th>Bytes</th>
              <th>Idle Timeout</th>
              <th>Priority</th>
              <th>Match Fields</th>
              <th>Actions</th>
              <th>Delete</th>
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
        <h4>Raw dump-flows</h4>
        <pre>{{ flowDump }}</pre>
      </div>
    </div>

    <div v-if="isArpTableTab">
      <div class="arp-table">
        <table>
          <thead>
            <tr>
              <th>IP Address</th>
              <th>MAC Address</th>
              <th>Interface</th>
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
