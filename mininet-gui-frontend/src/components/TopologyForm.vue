<template>
    <div>
      <form @submit.prevent="submitForm">
        <label for="type">Topology Type:</label>
        <select id="type" v-model="topologyType">
          <option value="Single">Single</option>
          <option value="Linear">Linear</option>
          <option value="Tree">Tree</option>
        </select>
        <br>
  
        <label for="nDevices">nDevices:</label>
        <input id="nDevices" type="text" v-model="nDevices" required />
        <br>
        <div v-if="topologyType === 'Tree'" class="tree-options">
          <label for="nLayers">nLayers:</label>
          <input id="nLayers" type="number" v-model="nLayers" required />
        </div>
        <br>
        <button class="submit-button" type="submit">Submit</button>
      </form>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        topologyType: "default",
        nDevices: "",
        nLayers: "",
      };
    },
    methods: {
      submitForm() {
        const formData = {
          type: this.topologyType,
          nDevices: this.nDevices,
          nLayers: this.topologyType === "Tree" ? this.nLayers : null,
        };
        this.$emit("form-submit", formData);
      },
    },
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
  </style>
  