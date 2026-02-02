<template>
  <div class="controller-form">
    <form class="controller-form__body" @submit.prevent="submitForm">
      <div class="controller-form__title">
        {{ titleText }}
      </div>
      <div class="controller-form__fields">
        <template v-if="isRemote">
          <label class="controller-form__label" for="ip">{{ $t("controller.ip") }}</label>
          <input
            id="ip"
            class="controller-form__input"
            type="text"
            v-model="ip"
            :disabled="isEditMode && !isEditing"
            required
          />
        </template>

        <label class="controller-form__label" for="port">{{ $t("controller.port") }}</label>
        <input
          id="port"
          class="controller-form__input"
          type="number"
          v-model="port"
          :disabled="(isEditMode && !isEditing) || isDefault"
          required
        />

        <template v-if="isRyu">
          <label class="controller-form__label" for="ryu-app">{{ $t("controller.ryuApp") }}</label>
          <select
            id="ryu-app"
            class="controller-form__select"
            v-model="ryuApp"
            :disabled="isEditMode && !isEditing"
            required
          >
            <option value="" disabled>{{ $t("controller.selectRyuApp") }}</option>
            <option v-for="app in ryuApps" :key="app" :value="app">{{ app }}</option>
          </select>
        </template>

        <label class="controller-form__label">{{ $t("controller.color") }}</label>
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

      <div class="controller-form__actions">
        <button
          v-if="isEditMode && !isEditing"
          class="controller-form__submit"
          type="button"
          @click="startEdit"
        >
          {{ $t("actions.edit") }}
        </button>
        <div v-else-if="isEditMode" class="controller-form__edit-actions">
          <button class="controller-form__submit" type="submit">{{ $t("actions.save") }}</button>
          <button class="controller-form__cancel" type="button" @click="cancelEdit">{{ $t("actions.cancel") }}</button>
        </div>
        <button v-else class="controller-form__submit" type="submit">{{ $t("actions.create") }}</button>
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

.controller-form__select:focus {
  outline: 2px solid #777;
  box-shadow: 0 0 0 2px #777;
}

.controller-form__select option:checked {
  background-color: #b3b3b3;
  color: #000;
}

.controller-form__actions {
  display: flex;
  justify-content: flex-end;
}

.controller-form__edit-actions {
  display: flex;
  gap: 8px;
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

.controller-form__cancel {
  border: 1px solid #c8c8c8;
  background: #ffffff;
  color: #1e1e1e;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 6px;
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
  border-color: #111827;
}

.controller-form__color:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.controller-form__color-check {
  line-height: 1;
}
</style>
