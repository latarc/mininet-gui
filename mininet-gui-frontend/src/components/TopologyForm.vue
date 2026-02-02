<template>
  <div class="modal-ui topology-form">
    <form class="modal-section" @submit.prevent="submitForm">
      <div class="modal-section__header">
        <div class="modal-section__title">{{ $t("topology.createTitle") }}</div>
      </div>
      <div class="modal-form-grid">
        <label class="modal-field" for="type">
          {{ $t("topology.type") }}
          <select id="type" v-model="topologyType" class="modal-select">
            <option value="Single" selected="selected">{{ $t("topology.single") }}</option>
            <option value="Linear">{{ $t("topology.linear") }}</option>
            <option value="Tree">{{ $t("topology.tree") }}</option>
          </select>
        </label>
        <label class="modal-field" for="controller">
          {{ $t("topology.controller") }}
          <select id="controller" v-model="controller" class="modal-select">
            <option value="" selected="selected">{{ $t("topology.none") }}</option>
            <option v-for="(v, k) of controllers" :key="k" :value="k">{{ k }}</option>
          </select>
        </label>
        <label v-if="topologyType === 'Single'" class="modal-field" for="nDevices">
          {{ $t("topology.hosts") }}
          <input id="nDevices" type="number" v-model="nDevices" class="modal-input" required />
        </label>
        <label v-if="topologyType === 'Linear'" class="modal-field" for="nDevices">
          {{ $t("topology.switches") }}
          <input id="nDevices" type="number" v-model="nDevices" class="modal-input" required />
        </label>
        <label v-if="topologyType === 'Linear'" class="modal-field" for="nLayers">
          {{ $t("topology.hostsPerSwitch") }}
          <input id="nLayers" type="number" v-model="nLayers" class="modal-input" required />
        </label>
        <label v-if="topologyType === 'Tree'" class="modal-field" for="nLayers">
          {{ $t("topology.layers") }}
          <input id="nLayers" type="number" v-model="nLayers" class="modal-input" required />
        </label>
        <label v-if="topologyType === 'Tree'" class="modal-field" for="nDevices">
          {{ $t("topology.fanout") }}
          <input id="nDevices" type="number" v-model="nDevices" class="modal-input" required />
        </label>
      </div>
      <div class="modal-actions">
        <button class="modal-button modal-button--primary" type="submit">{{ $t("actions.submit") }}</button>
      </div>
    </form>
  </div>
</template>

<script>
  export default {
    props: {
      controllers: new Object(),
    },
    data() {
      return {
        topologyType: "Single",
        nDevices: "",
        nLayers: null,
        controller: null,
      };
    },
    methods: {
      submitForm() {
        const formData = {
          type: this.topologyType,
          nDevices: this.nDevices,
          nLayers: this.nLayers,
          controller: this.controller,
        };
        this.$emit("form-submit", formData);
      },
    }
  };
</script>

<style scoped>
.topology-form .modal-form-grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}
</style>
