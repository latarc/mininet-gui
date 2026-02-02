<script setup>
import NetworkGraph from "./components/NetworkGraph.vue";
</script>

<template>
  <NetworkGraph />
</template>

<style>
@import url("https://fonts.googleapis.com/css?family=Fira Sans");

html {
  height: 100%;
  width: 100%;
}

:root {
  /* CSS HEX */
  --middle-blue: #89d2dcff;
  --slate-blue: #6564dbff;
  --persian-blue: #232ed1ff;
  --oxford-blue: #101d42ff;
  --rich-black-fogra-29: #0d1317ff;
}

body {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  background-color: var(--oxford-blue);
}

html.theme-light body {
  background-color: #f5f5f5;
}

html.theme-dark body {
  background-color: var(--oxford-blue);
}

#app {
  /* display: flex;
    flex-direction: column; */
  display: block;
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
