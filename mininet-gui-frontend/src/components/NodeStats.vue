<script>
export default {
  props: ["stats"],
  data() {
    return {
      activeTab: "details",
      tabs: [
        { key: "details", label: "Details" }
      ]
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
      const { flow_table, arp_table, ...details } = this.stats || {};
      return details;
    }
  },
  methods: {
    setTab(tabKey) {
      this.activeTab = tabKey;
    },
    formatMatchFields(matchFields) {
      return Object.entries(matchFields).map(([key, value]) => `${key}: ${value}`).join(', ');
    }
  },
  created() {
    if (this.stats?.type === "sw") {
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
            </tr>
          </thead>
          <tbody>
            <tr v-for="(flow, index) in stats.flow_table" :key="index">
              <td>{{ index + 1 }}</td>
              <td>{{ flow.cookie }}</td>
              <td>{{ flow.duration }}</td>
              <td>{{ flow.table }}</td>
              <td>{{ flow.n_packets }}</td>
              <td>{{ flow.n_bytes }}</td>
              <td>{{ flow.idle_timeout }}</td>
              <td>{{ flow.priority }}</td>
              <td>{{ formatMatchFields(flow.match_fields) }}</td>
            </tr>
          </tbody>
        </table>
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
            <tr v-for="entry in stats.arp_table" :key="entry.ip">
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
