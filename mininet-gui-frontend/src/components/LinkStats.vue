<template>
  <div class="link-modal">
    <div class="link-header">
      <div class="link-title">{{ linkLabel }}</div>
      <button class="link-refresh" type="button" :disabled="statsBusy" @click="loadStats">
        {{ $t("actions.refresh") }}
      </button>
    </div>

    <div class="link-section">
      <h4>{{ $t("link.optionsTitle") }}</h4>
      <div class="link-form">
        <label>
          {{ $t("link.bandwidth") }}
          <input v-model="form.bw" type="number" min="0" step="1" />
        </label>
        <label>
          {{ $t("link.delay") }}
          <input v-model="form.delay" type="number" min="0" step="1" />
        </label>
        <label>
          {{ $t("link.jitter") }}
          <input v-model="form.jitter" type="number" min="0" step="1" />
        </label>
        <label>
          {{ $t("link.loss") }}
          <input v-model="form.loss" type="number" min="0" max="100" step="0.1" />
        </label>
        <label>
          {{ $t("link.maxQueue") }}
          <input v-model="form.max_queue_size" type="number" min="0" step="1" />
        </label>
        <label class="link-checkbox">
          <input v-model="form.use_htb" type="checkbox" />
          {{ $t("link.useHtb") }}
        </label>
      </div>
      <div class="link-actions">
        <button type="button" class="link-save" :disabled="saveBusy" @click="saveOptions">
          {{ saveBusy ? $t("actions.saving") : $t("link.saveOptions") }}
        </button>
        <span v-if="saveError" class="link-error">{{ saveError }}</span>
        <span v-else-if="saveSuccess" class="link-success">{{ $t("actions.saved") }}</span>
      </div>
    </div>

    <div class="link-section">
      <h4>{{ $t("link.statsTitle") }}</h4>
      <div v-if="statsError" class="link-error">{{ statsError }}</div>
      <div v-else class="link-stats">
        <div v-if="stats?.intfs?.length" class="link-stats-table">
          <div class="link-stats-row header">
            <span>{{ $t("link.interface") }}</span>
            <span>{{ $t("link.tx") }}</span>
            <span>{{ $t("link.rx") }}</span>
          </div>
          <div v-for="intf in stats.intfs" :key="intf.name" class="link-stats-row">
            <span>{{ intf.name }}</span>
            <span>{{ formatBytes(intf.tx_bytes) }}</span>
            <span>{{ formatBytes(intf.rx_bytes) }}</span>
          </div>
        </div>
        <div v-else class="link-empty">{{ $t("link.noStats") }}</div>
        <div class="link-timestamp" v-if="stats?.timestamp">
          {{ $t("link.updatedAt", { time: formatTimestamp(stats.timestamp) }) }}
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
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #111827;
}

.link-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.link-title {
  font-weight: 600;
}

.link-section h4 {
  margin: 0 0 8px;
  font-weight: 600;
}

.link-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(140px, 1fr));
  gap: 10px 16px;
}

.link-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
}

.link-form input[type="number"] {
  background: #1e1e1e;
  color: #e5e7eb;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  padding: 6px 8px;
}

.link-checkbox {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.link-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.link-save,
.link-refresh {
  border: 1px solid #2a2a2a;
  background: #1a1a1a;
  color: #fff;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.link-save:disabled,
.link-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.link-error {
  color: #ff6b6b;
  font-size: 0.85rem;
}

.link-success {
  color: #9be2a5;
  font-size: 0.85rem;
}

.link-stats-table {
  display: grid;
  gap: 6px;
}

.link-stats-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 8px;
  font-size: 0.85rem;
}

.link-stats-row.header {
  font-weight: 600;
  color: #9da9b7;
}

.link-empty {
  color: #8a8a8a;
  font-size: 0.85rem;
}

.link-timestamp {
  margin-top: 8px;
  font-size: 0.75rem;
  color: #8a8a8a;
}
</style>
