<template>
    <div>
      <form @submit.prevent="submitForm">
        <label for="type">Controller Type:</label>
        <select id="type" v-model="controllerType">
          <option value="default">Default</option>
          <option value="remote">Remote</option>
        </select>
  
        <div v-if="controllerType === 'remote'" class="remote-options">
          <label for="ip">IP:</label>
          <input id="ip" type="text" v-model="ip" required />
  
          <label for="port">Port:</label>
          <input id="port" type="number" v-model="port" required />
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
        controllerType: "default",
        ip: "",
        port: "",
      };
    },
    methods: {
      submitForm() {
        const formData = {
          type: this.controllerType,
          ip: this.controllerType === "remote" ? this.ip : null,
          port: this.controllerType === "remote" ? this.port : null,
        };
        this.$emit("form-submit", formData);
      },
    },
  };
  </script>
  
  <style scoped>
  .remote-options {
    margin-top: 1rem;
  }

  label {
    color: black;
  }
  
  .submit-button {
    float: right;

  }
  </style>
  