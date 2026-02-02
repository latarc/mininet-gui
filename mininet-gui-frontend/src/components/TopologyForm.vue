<template>
  <div>
    <form @submit.prevent="submitForm">
      <div>
        <label for="type">{{ $t("topology.type") }}</label>
        <select id="type" v-model="topologyType">
          <option value="Single" selected="selected">{{ $t("topology.single") }}</option>
          <option value="Linear">{{ $t("topology.linear") }}</option>
          <option value="Tree">{{ $t("topology.tree") }}</option>
        </select>
      </div>
      <div>
        <label for="controller">{{ $t("topology.controller") }}</label>
        <select id="controller" v-model="controller">
          <option value="" selected="selected">{{ $t("topology.none") }}</option>
          <option v-for="(v, k) of controllers" :key="k" :value="k">{{k}}</option>
        </select>
      </div>
      <div v-if="topologyType === 'Single'">
        <label for="nDevices">{{ $t("topology.hosts") }}</label>
        <input id="nDevices" type="number" v-model="nDevices" required />
      </div>
      <div v-if="topologyType === 'Linear'" class="tree-options">
        <div>
          <label for="nDevices">{{ $t("topology.switches") }}</label>
          <input id="nDevices" type="number" v-model="nDevices" required />
        </div>
        <div>
          <label for="nLayers">{{ $t("topology.hostsPerSwitch") }}</label>
          <input id="nLayers" type="number" v-model="nLayers" required />
        </div>
      </div>
      <div v-if="topologyType === 'Tree'" class="tree-options">
        <div>
          <label for="nLayers">{{ $t("topology.layers") }}</label>
          <input id="nLayers" type="number" v-model="nLayers" required />
        </div>
        <div>
          <label for="nDevices">{{ $t("topology.fanout") }}</label>
          <input id="nDevices" type="number" v-model="nDevices" required />
        </div>
      </div>
      <button class="submit-button" type="submit">{{ $t("actions.submit") }}</button>
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
  .tree-options {
    margin-top: 1rem;
  }

  label {
    color: black;
  }
  
  .submit-button {
    float: right;
  }

  input {
    width: 80px;
  }

  select:focus {
    outline: 2px solid #777;
    box-shadow: 0 0 0 2px #777;
  }

  select option:checked {
    background-color: #b3b3b3;
    color: #000;
  }
  </style>
