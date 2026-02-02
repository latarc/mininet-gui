<template>
  <div class="modal-ui controller-form">
    <form class="modal-section controller-form__body" @submit.prevent="submitForm">
      <div class="modal-section__header">
        <div class="modal-section__title">{{ titleText }}</div>
      </div>
      <div class="modal-form-grid">
        <template v-if="isRemote">
          <label class="modal-field" for="ip">
            {{ $t("controller.ip") }}
            <input
              id="ip"
              class="modal-input"
              type="text"
              v-model="ip"
              :disabled="isEditMode && !isEditing"
              required
            />
          </label>
        </template>

        <label class="modal-field" for="port">
          {{ $t("controller.port") }}
          <input
            id="port"
            class="modal-input"
            type="number"
            v-model="port"
            :disabled="(isEditMode && !isEditing) || isDefault"
            required
          />
        </label>

        <template v-if="isRyu">
          <label class="modal-field" for="ryu-app">
            {{ $t("controller.ryuApp") }}
            <select
              id="ryu-app"
              class="modal-select"
              v-model="ryuApp"
              :disabled="isEditMode && !isEditing"
              required
            >
              <option value="" disabled>{{ $t("controller.selectRyuApp") }}</option>
              <option v-for="app in ryuApps" :key="app" :value="app">{{ app }}</option>
            </select>
          </label>
        </template>

        <div class="modal-field">
          {{ $t("controller.color") }}
          <div class="controller-form__colors">
          <button
            v-for="color in colorChoices"
            :key="color"
            type="button"
            class="controller-form__color"
            :class="{ selected: color === colorCode }"
            :style="{ backgroundColor: color }"
            @click="selectColor(color)"
          >
            <span v-if="color === colorCode" class="controller-form__color-check">✓</span>
          </button>
          </div>
        </div>
      </div>

      <div class="modal-actions">
        <button
          v-if="isEditMode && !isEditing"
          class="modal-button"
          type="button"
          @click="startEdit"
        >
          {{ $t("actions.edit") }}
        </button>
        <div v-else-if="isEditMode" class="controller-form__edit-actions">
          <button class="modal-button modal-button--primary" type="submit">{{ $t("actions.save") }}</button>
          <button class="modal-button" type="button" @click="cancelEdit">{{ $t("actions.cancel") }}</button>
        </div>
        <button v-else class="modal-button modal-button--primary" type="submit">{{ $t("actions.create") }}</button>
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
    controller: {
      type: Object,
      default: null,
    },
  },
  emits: ["form-submit", "form-update"],
  data() {
    return {
      type: this.presetType || "remote",
      ip: "127.0.0.1",
      port: "",
      ryuApp: "",
      colorCode: "#ffffff",
      isEditing: false,
      colorChoices: ["#ffffff", "#007acc", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"],
    };
  },
  computed: {
    isRyu() {
      return this.type === "ryu";
    },
    isRemote() {
      return this.type === "remote";
    },
    isDefault() {
      return this.type === "default";
    },
    isEditMode() {
      return !!this.controller;
    },
    titleText() {
      if (this.isEditMode) return this.$t("controller.title");
      return this.isRyu ? this.$t("controller.ryuTitle") : this.$t("controller.remoteTitle");
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
    controller: {
      immediate: true,
      handler(value) {
        if (!value) return;
        this.type = (value.controller_type || "").toLowerCase() || "remote";
        this.ip = value.ip || "127.0.0.1";
        this.port = value.port ?? "";
        this.ryuApp = value.ryu_app || "";
        this.colorCode = value.color || "#ffffff";
        this.isEditing = false;
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
      this.colorCode = "#ffffff";
      this.isEditing = false;
    },
    selectColor(color) {
      if (this.isEditMode && !this.isEditing) {
        this.isEditing = true;
      }
      this.colorCode = color;
    },
    startEdit() {
      this.isEditing = true;
    },
    cancelEdit() {
      if (this.controller) {
        this.type = (this.controller.controller_type || "").toLowerCase() || "remote";
        this.ip = this.controller.ip || "127.0.0.1";
        this.port = this.controller.port ?? "";
        this.ryuApp = this.controller.ryu_app || "";
        this.colorCode = this.controller.color || "#ffffff";
      }
      this.isEditing = false;
    },
    submitForm() {
      const formData = {
        type: this.type,
        ip: this.isRyu ? "127.0.0.1" : this.ip,
        port: Number(this.port),
        ryu_app: this.isRyu ? this.ryuApp : null,
        color: this.colorCode,
      };
      if (this.isEditMode) {
        this.$emit("form-update", formData);
        this.isEditing = false;
      } else {
        this.$emit("form-submit", formData);
      }
    },
  },
};
</script>

<style scoped>
.controller-form__edit-actions {
  display: flex;
  gap: 8px;
}

.controller-form__colors {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.controller-form__color {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: 2px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
}

.controller-form__color.selected {
  border-color: #f8fafc;
}

.controller-form__color:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.controller-form__color-check {
  line-height: 1;
}
</style>
