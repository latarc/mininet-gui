<template>
  <div class="controller-form">
    <form class="controller-form__body" @submit.prevent="submitForm">
      <div class="controller-form__title">
        {{ isRyu ? "Ryu Controller" : "Remote Controller" }}
      </div>
      <div class="controller-form__fields">
        <template v-if="isRemote">
          <label class="controller-form__label" for="ip">IP</label>
          <input id="ip" class="controller-form__input" type="text" v-model="ip" required />
        </template>

        <label class="controller-form__label" for="port">Port</label>
        <input id="port" class="controller-form__input" type="number" v-model="port" required />

        <template v-if="isRyu">
          <label class="controller-form__label" for="ryu-app">Ryu app</label>
          <select id="ryu-app" class="controller-form__select" v-model="ryuApp" required>
            <option value="" disabled>Select ryu app</option>
            <option v-for="app in ryuApps" :key="app" :value="app">{{ app }}</option>
          </select>
        </template>
      </div>

      <div class="controller-form__actions">
        <button class="controller-form__submit" type="submit">Create</button>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  props: {
    presetType: {
      type: String,
      default: null,
    },
    ryuApps: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      type: this.presetType || "remote",
      ip: "127.0.0.1",
      port: "",
      ryuApp: "",
    };
  },
  computed: {
    isRyu() {
      return this.type === "ryu";
    },
    isRemote() {
      return this.type === "remote";
    },
  },
  watch: {
    presetType: {
      immediate: true,
      handler(newType) {
        this.type = newType || "remote";
        this.resetForm();
      },
    },
    ryuApps() {
      if (this.isRyu && !this.ryuApp && this.ryuApps.length) {
        this.ryuApp = this.ryuApps[0];
      }
    },
  },
  methods: {
    resetForm() {
      this.ip = "127.0.0.1";
      this.port = "";
      this.ryuApp = this.ryuApps.length ? this.ryuApps[0] : "";
    },
    submitForm() {
      const formData = {
        type: this.type,
        ip: this.isRyu ? "127.0.0.1" : this.ip,
        port: Number(this.port),
        ryu_app: this.isRyu ? this.ryuApp : null,
      };
      this.$emit("form-submit", formData);
    },
  },
};
</script>

<style scoped>
.controller-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.controller-form__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.controller-form__title {
  font-size: 14px;
  font-weight: 600;
  color: #1e1e1e;
}

.controller-form__fields {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.controller-form__label {
  font-size: 12px;
  font-weight: 600;
  color: #1e1e1e;
}

.controller-form__input,
.controller-form__select {
  width: 100%;
  border: 1px solid #c8c8c8;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  background: #ffffff;
  color: #1e1e1e;
}

.controller-form__actions {
  display: flex;
  justify-content: flex-end;
}

.controller-form__submit {
  border: 1px solid #007acc;
  background: #007acc;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 6px;
}
</style>
