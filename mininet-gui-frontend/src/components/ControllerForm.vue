<template>
    <div>
      <form @submit.prevent="submitForm">
        <div class="controller-type">Remote Controller</div>
        <div class="remote-options">
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
        ip: "",
        port: "",
      };
    },
    methods: {
      submitForm() {
        const formData = {
          type: "remote",
          ip: this.ip,
          port: this.port,
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

  .controller-type {
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: black;
  }

  label {
    color: black;
  }
  
  .submit-button {
    float: right;

  }
  </style>
  
