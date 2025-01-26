<script>
export default {
  props: ["stats"], // Removed modalOption
  data() {
    return {
      activeTab: "details", // Local state for tabs
      tabs: [
        { key: "details", label: "Details" },
        { key: "flows", label: "Flow Table" }
      ]
    };
  },
  computed: {
    isDetailsTab() {
      return this.activeTab === "details";
    },
    isFlowTableTab() {
      return this.activeTab === "flows";
    }
  },
  methods: {
    setTab(tabKey) {
      this.activeTab = tabKey; // Update internal state
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
          <li v-for="(value, key) in stats" :key="key">
            <strong>{{ key }}:</strong> {{ value }}
          </li>
        </ul>
      </div>
  
      <div v-if="isFlowTableTab">
        <div class="flow-table">
          <div v-for="(flow, index) in stats?.flow_table" :key="index" class="flow-item">
            <strong>Rule {{ index + 1 }}</strong>
            <ul>
              <li v-for="(val, key) in flow" :key="key">
                <strong>{{ key }}:</strong> {{ val }}
              </li>
            </ul>
          </div>
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
    width: 400px;  /* Fixed width */
    height: 300px; /* Fixed height */
    overflow-y: auto; /* Enable vertical scroll */
    text-align: left; /* Left-align text */
    padding: 10px;
    border: 1px solid #ccc;
    background: #fff;
  }
  
  .stats-list, .flow-table {
    list-style: none;
    padding: 0;
  }
  
  .flow-item {
    margin-bottom: 12px;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 5px;
    background: #f9f9f9;
  }
  </style>
  