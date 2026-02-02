<script setup>
import { computed } from "vue";
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
});

const emit = defineEmits(["close"]);

const open = computed({
  get: () => props.show,
  set: (value) => {
    if (!value) emit("close");
  },
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
          'fixed left-[50%] top-[50%] z-50 flex flex-col translate-x-[-50%] translate-y-[-50%] border bg-background p-0 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg',
          sizeClass,
          contentClass,
        ]"
      >
        <div class="flex items-start justify-between gap-3 border-b bg-gradient-to-b from-slate-50 to-white px-6 py-5">
          <DialogTitle class="text-left text-lg font-semibold tracking-tight">
            <slot name="header">{{ $t("modal.defaultHeader") }}</slot>
          </DialogTitle>
          <DialogClose
            class="rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
            aria-label="Close"
          >
            <span aria-hidden="true">x</span>
          </DialogClose>
        </div>
        <div
          :class="[
            'flex-1 min-h-0 overflow-auto px-6 pb-6 pt-4 text-left text-slate-700',
            bodyClass,
          ]"
        >
          <slot name="body">{{ $t("modal.defaultBody") }}</slot>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
