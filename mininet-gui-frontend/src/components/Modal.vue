<script setup>
import { computed, onBeforeUnmount, ref, watch, nextTick } from "vue";
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogClose } from "radix-vue";

const props = defineProps({
  show: Boolean,
  sizeClass: {
    type: String,
    default: "w-fit min-w-[320px] max-w-[90vw] max-h-[85vh]",
  },
  contentClass: {
    type: String,
    default: "",
  },
  bodyClass: {
    type: String,
    default: "",
  },
  theme: {
    type: String,
    default: "dark",
  },
});

const emit = defineEmits(["close"]);

const open = computed({
  get: () => props.show,
  set: (value) => {
    if (!value) emit("close");
  },
});

const isLightTheme = computed(() => props.theme === "light");
const themeClass = computed(() => (isLightTheme.value ? "theme-light" : "theme-dark"));

const modalBodyRef = ref(null);
const tabPanelSize = ref({ width: 0, height: 0 });
const tabPanelStyle = computed(() => {
  if (!tabPanelSize.value.width && !tabPanelSize.value.height) return {};
  return {
    "--modal-tab-panel-min-width": tabPanelSize.value.width ? `${tabPanelSize.value.width}px` : "0px",
    "--modal-tab-panel-min-height": tabPanelSize.value.height ? `${tabPanelSize.value.height}px` : "0px",
  };
});

let tabPanelsContainer = null;
let resizeObserver = null;
let mutationObserver = null;
let measurementFrame = 0;

const measureTabPanels = () => {
  if (!tabPanelsContainer) {
    tabPanelSize.value = { width: 0, height: 0 };
    return;
  }

  const panels = Array.from(tabPanelsContainer.querySelectorAll(".tab-panel"));
  if (!panels.length) {
    tabPanelSize.value = { width: 0, height: 0 };
    return;
  }

  let maxWidth = 0;
  let maxHeight = 0;
  panels.forEach((panel) => {
    const rect = panel.getBoundingClientRect();
    maxWidth = Math.max(maxWidth, rect.width);
    maxHeight = Math.max(maxHeight, rect.height);
  });

  const nextWidth = Math.max(0, Math.ceil(maxWidth));
  const nextHeight = Math.max(0, Math.ceil(maxHeight));

  if (tabPanelSize.value.width !== nextWidth || tabPanelSize.value.height !== nextHeight) {
    tabPanelSize.value = { width: nextWidth, height: nextHeight };
  }
};

const scheduleMeasurement = () => {
  if (measurementFrame) return;
  measurementFrame = requestAnimationFrame(() => {
    measurementFrame = 0;
    measureTabPanels();
  });
};

const disconnectObservers = () => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (mutationObserver) {
    mutationObserver.disconnect();
    mutationObserver = null;
  }
};

const refreshTabObservers = () => {
  const container = modalBodyRef.value?.querySelector(".modal-tab-panels") || null;
  tabPanelsContainer = container;
  if (!container) {
    tabPanelSize.value = { width: 0, height: 0 };
    disconnectObservers();
    return;
  }

  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  resizeObserver = new ResizeObserver(() => scheduleMeasurement());
  Array.from(container.querySelectorAll(".tab-panel")).forEach((panel) => {
    resizeObserver.observe(panel);
  });

  if (mutationObserver) {
    mutationObserver.disconnect();
  }
  mutationObserver = new MutationObserver(() => refreshTabObservers());
  mutationObserver.observe(container, { childList: true, subtree: true, attributes: false });

  scheduleMeasurement();
};

watch(
  () => props.show,
  (visible) => {
    if (visible) {
      nextTick(() => {
        refreshTabObservers();
      });
      return;
    }

    tabPanelSize.value = { width: 0, height: 0 };
    tabPanelsContainer = null;
    disconnectObservers();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (measurementFrame) {
    cancelAnimationFrame(measurementFrame);
  }
  disconnectObservers();
});
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay
        class="fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
      />
      <DialogContent
        :class="[
          'modal-surface fixed left-[50%] top-[50%] z-50 flex flex-col translate-x-[-50%] translate-y-[-50%] p-0 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg',
          themeClass,
          sizeClass,
          contentClass,
        ]"
      >
        <div class="modal-header flex items-start justify-between gap-3 px-6 py-5">
          <DialogTitle class="modal-title text-left text-lg font-semibold tracking-tight">
            <slot name="header">{{ $t("modal.defaultHeader") }}</slot>
          </DialogTitle>
          <DialogClose
            class="modal-close rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none"
            aria-label="Close"
          >
            <span aria-hidden="true">x</span>
          </DialogClose>
        </div>
        <div
          ref="modalBodyRef"
          :class="[
            'modal-body flex-1 min-h-0 overflow-auto px-6 pb-6 pt-4 text-left',
            bodyClass,
          ]"
          :style="tabPanelStyle"
        >
          <slot name="body">{{ $t("modal.defaultBody") }}</slot>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style>
.modal-surface {
  background: #1e1e1e;
  border: 1px solid #333333;
  color: #cccccc;
}

.modal-header {
  border-bottom: 1px solid #333333;
  background: #1d1d1d;
}

.modal-title {
  color: #cccccc;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.modal-close {
  color: #9b9b9b;
}

.modal-close:focus {
  outline: 2px solid #007acc;
  box-shadow: 0 0 0 2px #007acc;
}

.modal-body {
  color: #cccccc;
}

.modal-ui {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-section {
  background: #2a2a2a;
  border: 1px solid #333333;
  border-radius: 10px;
  padding: 12px 16px;
}

.modal-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.modal-section__title {
  font-size: 13px;
  font-weight: 600;
  color: #cccccc;
}

.modal-muted {
  color: #9b9b9b;
  font-size: 12px;
}

.modal-divider {
  height: 1px;
  background: #333333;
  border: none;
  margin: 12px 0;
}

.modal-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-bottom: 1px solid #333333;
  padding-bottom: 10px;
}

.modal-tab {
  border: 1px solid #333333;
  border-radius: 8px;
  padding: 6px 12px;
  background: #2d2d2d;
  color: #cccccc;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.modal-tab:hover {
  background: #3e3e3e;
  color: #f2f2f2;
}

.modal-tab.is-active {
  background: #0b2b3b;
  color: #e6f2ff;
  border-color: #007acc;
  box-shadow: inset 0 0 0 1px #007acc;
}

.modal-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #cccccc;
}

.modal-input,
.modal-select,
.modal-textarea {
  background: #2d2d2d;
  color: #e6e6e6;
  border: 1px solid #333333;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
}

.modal-input::placeholder,
.modal-textarea::placeholder {
  color: #888888;
}

.modal-input:focus,
.modal-select:focus,
.modal-textarea:focus {
  outline: 2px solid #007acc;
  box-shadow: 0 0 0 2px #007acc;
}

.modal-select option:checked {
  background-color: #007acc;
  color: #f2f2f2;
}

.modal-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.modal-button {
  border: 1px solid #333333;
  background: #2d2d2d;
  color: #cccccc;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.modal-button:hover {
  background: #3e3e3e;
}

.modal-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-button--primary {
  background: #007acc;
  border-color: #007acc;
  color: #e6f2ff;
}

.modal-button--primary:hover {
  background: #0084e6;
}

.modal-button--danger {
  background: #c62828;
  border-color: #c62828;
  color: #f2f2f2;
}

.modal-button--danger:hover {
  background: #a61f1f;
}

.modal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.modal-table th,
.modal-table td {
  border-bottom: 1px solid #333333;
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}

.modal-table thead th {
  color: #9b9b9b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 11px;
}

.modal-table tbody th {
  color: #cccccc;
  font-weight: 600;
  text-transform: none;
}

.modal-table tbody tr:hover {
  background: #252525;
}

.modal-table--compact th,
.modal-table--compact td {
  padding: 6px 8px;
}

.modal-table__wrapper {
  width: 100%;
  overflow: auto;
  border: 1px solid #333333;
  border-radius: 10px;
}

.modal-pre {
  background: #2d2d2d;
  border: 1px solid #333333;
  color: #e6e6e6;
  padding: 12px;
  border-radius: 10px;
  font-size: 12px;
  white-space: pre-wrap;
}

.modal-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #2d2d2d;
  border: 1px solid #333333;
  font-size: 11px;
  color: #cccccc;
}

.modal-error {
  color: #f28b82;
  font-size: 12px;
}

.modal-success {
  color: #61efb5;
  font-size: 12px;
}

.modal-tab-panels {
  display: grid;
  grid-template-areas: "stack";
  align-items: start;
  min-width: var(--modal-tab-panel-min-width, 0);
  min-height: var(--modal-tab-panel-min-height, 0);
}

.modal-tab-panels > .tab-panel {
  grid-area: stack;
}

.modal-tab-panels > .tab-panel.is-hidden {
  visibility: hidden;
  pointer-events: none;
}

.theme-light .modal-surface {
  background: #ffffff;
  border: 1px solid #d0d0d0;
  color: #2b2b2b;
}

.theme-light .modal-header {
  border-bottom: 1px solid #d0d0d0;
  background: #f5f5f5;
}

.theme-light .modal-title {
  color: #2b2b2b;
}

.theme-light .modal-close {
  color: #6b6b6b;
}

.theme-light .modal-body {
  color: #2b2b2b;
}

.theme-light .modal-section {
  background: #f7f7f7;
  border: 1px solid #d0d0d0;
}

.theme-light .modal-section__title {
  color: #2b2b2b;
}

.theme-light .modal-muted {
  color: #6b6b6b;
}

.theme-light .modal-divider {
  background: #d0d0d0;
}

.theme-light .modal-tabs {
  border-bottom: 1px solid #d0d0d0;
}

.theme-light .modal-tab {
  border: 1px solid #d0d0d0;
  background: #f5f5f5;
  color: #2b2b2b;
}

.theme-light .modal-tab:hover {
  background: #e6e6e6;
  color: #1f1f1f;
}

.theme-light .modal-tab.is-active {
  background: #e6f2ff;
  color: #0b2b3b;
  border-color: #007acc;
  box-shadow: inset 0 0 0 1px #007acc;
}

.theme-light .modal-field {
  color: #2b2b2b;
}

.theme-light .modal-input,
.theme-light .modal-select,
.theme-light .modal-textarea {
  background: #ffffff;
  color: #2b2b2b;
  border: 1px solid #d0d0d0;
}

.theme-light .modal-input::placeholder,
.theme-light .modal-textarea::placeholder {
  color: #888888;
}

.theme-light .modal-select option:checked {
  background-color: #007acc;
  color: #ffffff;
}

.theme-light .modal-button {
  border: 1px solid #d0d0d0;
  background: #f5f5f5;
  color: #2b2b2b;
}

.theme-light .modal-button:hover {
  background: #e6e6e6;
}

.theme-light .modal-table th,
.theme-light .modal-table td {
  border-bottom: 1px solid #d0d0d0;
}

.theme-light .modal-table thead th {
  color: #6b6b6b;
}

.theme-light .modal-table tbody th {
  color: #2b2b2b;
}

.theme-light .modal-table tbody tr:hover {
  background: #f0f0f0;
}

.theme-light .modal-table__wrapper {
  border: 1px solid #d0d0d0;
}

.theme-light .modal-pre {
  background: #f3f3f3;
  border: 1px solid #d0d0d0;
  color: #2b2b2b;
}

.theme-light .modal-pill {
  background: #f5f5f5;
  border: 1px solid #d0d0d0;
  color: #2b2b2b;
}
</style>
