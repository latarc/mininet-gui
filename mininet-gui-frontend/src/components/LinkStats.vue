<template>
  <div class="modal-ui link-modal">
    <div class="modal-tabs">
      <button type="button" class="modal-tab" :class="{ 'is-active': activeTab === 'options' }" @click="activeTab = 'options'">
        {{ $t("link.optionsTitle") }}
      </button>
      <button type="button" class="modal-tab" :class="{ 'is-active': activeTab === 'stats' }" @click="activeTab = 'stats'">
        {{ $t("link.statsTitle") }}
      </button>
    </div>

    <div class="modal-tab-panels">
      <div class="modal-section tab-panel" :class="{ 'is-hidden': activeTab !== 'options' }">
      <div class="modal-section__header">
        <div class="modal-section__title">{{ linkLabel }}</div>
        <span class="modal-muted">{{ $t("link.optionsTitle") }}</span>
      </div>
      <div class="modal-form-grid">
        <label class="modal-field">
          {{ $t("link.bandwidth") }}
          <input v-model="form.bw" type="number" min="0" step="1" class="modal-input" />
        </label>
        <label class="modal-field">
          {{ $t("link.delay") }}
          <input v-model="form.delay" type="number" min="0" step="1" class="modal-input" />
        </label>
        <label class="modal-field">
          {{ $t("link.jitter") }}
          <input v-model="form.jitter" type="number" min="0" step="1" class="modal-input" />
        </label>
        <label class="modal-field">
          {{ $t("link.loss") }}
          <input v-model="form.loss" type="number" min="0" max="100" step="0.1" class="modal-input" />
        </label>
        <label class="modal-field">
          {{ $t("link.maxQueue") }}
          <input v-model="form.max_queue_size" type="number" min="0" step="1" class="modal-input" />
        </label>
        <label class="modal-field link-checkbox">
          <input v-model="form.use_htb" type="checkbox" />
          <span>{{ $t("link.useHtb") }}</span>
        </label>
      </div>
      <div class="modal-actions">
        <button type="button" class="modal-button modal-button--primary" :disabled="saveBusy" @click="saveOptions">
          {{ saveBusy ? $t("actions.saving") : $t("link.saveOptions") }}
        </button>
        <span v-if="saveError" class="modal-error">{{ saveError }}</span>
        <span v-else-if="saveSuccess" class="modal-success">{{ $t("actions.saved") }}</span>
      </div>
      </div>

      <div class="modal-section tab-panel" :class="{ 'is-hidden': activeTab !== 'stats' }">
      <div class="modal-section__header">
        <div class="modal-section__title">{{ $t("link.statsTitle") }}</div>
        <button class="modal-button" type="button" :disabled="statsBusy" @click="loadStats">
          {{ $t("actions.refresh") }}
        </button>
      </div>
      <div v-if="statsError" class="modal-error">{{ statsError }}</div>
      <div v-else class="link-stats">
        <div v-if="stats?.intfs?.length" class="modal-table__wrapper">
          <table class="modal-table">
            <thead>
              <tr>
                <th>{{ $t("link.interface") }}</th>
                <th>{{ $t("link.tx") }}</th>
                <th>{{ $t("link.rx") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="intf in stats.intfs" :key="intf.name">
                <td>{{ intf.name }}</td>
                <td>{{ formatBytes(intf.tx_bytes) }}</td>
                <td>{{ formatBytes(intf.rx_bytes) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="modal-muted">{{ $t("link.noStats") }}</div>
        <div class="modal-muted link-timestamp" v-if="stats?.timestamp">
          {{ $t("link.updatedAt", { time: formatTimestamp(stats.timestamp) }) }}
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getLinkStats, updateLinkOptions } from "@/core/api";

export default {
  props: {
    link: { type: Object, required: true },
  },
  emits: ["linkUpdated"],
  data() {
    return {
      activeTab: "stats",
      form: {
        bw: "",
        delay: "",
        jitter: "",
        loss: "",
        max_queue_size: "",
        use_htb: false,
      },
      stats: null,
      statsBusy: false,
      statsError: "",
      saveBusy: false,
      saveError: "",
      saveSuccess: false,
    };
  },
  computed: {
    linkLabel() {
      return `${this.link?.from || ""} ↔ ${this.link?.to || ""}`;
    },
  },
  watch: {
    link: {
      immediate: true,
      handler(value) {
        if (!value) return;
        this.applyOptions(value.options || {});
        this.loadStats();
      },
    },
  },
  methods: {
    applyOptions(options) {
      this.form.bw = options?.bw ?? "";
      this.form.delay = options?.delay ?? "";
      this.form.jitter = options?.jitter ?? "";
      this.form.loss = options?.loss ?? "";
      this.form.max_queue_size = options?.max_queue_size ?? "";
      this.form.use_htb = !!options?.use_htb;
    },
    buildPayload() {
      const payload = {};
      if (this.form.bw !== "" && this.form.bw !== null) payload.bw = Number(this.form.bw);
      if (this.form.delay !== "" && this.form.delay !== null) payload.delay = Number(this.form.delay);
      if (this.form.jitter !== "" && this.form.jitter !== null) payload.jitter = Number(this.form.jitter);
      if (this.form.loss !== "" && this.form.loss !== null) payload.loss = Number(this.form.loss);
      if (this.form.max_queue_size !== "" && this.form.max_queue_size !== null) {
        payload.max_queue_size = Number(this.form.max_queue_size);
      }
      if (this.form.use_htb) payload.use_htb = true;
      return payload;
    },
    async loadStats() {
      if (!this.link?.from || !this.link?.to) return;
      this.statsBusy = true;
      this.statsError = "";
      try {
        const response = await getLinkStats(this.link.from, this.link.to);
        this.stats = response || null;
        if (response?.options) {
          this.applyOptions(response.options);
        }
      } catch (error) {
        this.statsError = this.$t("link.errorFetch");
      } finally {
        this.statsBusy = false;
      }
    },
    async saveOptions() {
      if (!this.link?.from || !this.link?.to) return;
      this.saveBusy = true;
      this.saveError = "";
      this.saveSuccess = false;
      try {
        const options = this.buildPayload();
        const response = await updateLinkOptions(this.link.from, this.link.to, options);
        if (!response) {
          this.saveError = this.$t("link.errorUpdate");
          return;
        }
        this.saveSuccess = true;
        this.$emit("linkUpdated", response.options || options);
        await this.loadStats();
      } catch (error) {
        this.saveError = this.$t("link.errorUpdate");
      } finally {
        this.saveBusy = false;
        setTimeout(() => {
          this.saveSuccess = false;
        }, 1500);
      }
    },
    formatBytes(value) {
      if (value == null || Number.isNaN(Number(value))) return "-";
      const num = Number(value);
      if (num < 1024) return `${num} B`;
      const units = ["KB", "MB", "GB", "TB"];
      let size = num;
      let idx = -1;
      while (size >= 1024 && idx < units.length - 1) {
        size /= 1024;
        idx += 1;
      }
      return `${size.toFixed(2)} ${units[idx]}`;
    },
    formatTimestamp(ts) {
      try {
        const date = new Date(ts);
        if (Number.isNaN(date.getTime())) return String(ts);
        return date.toLocaleTimeString();
      } catch (error) {
        return String(ts);
      }
    },
  },
};
</script>

<style scoped>
.link-modal {
  min-width: 420px;
}

.link-checkbox {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.link-timestamp {
  margin-top: 8px;
}
</style>
