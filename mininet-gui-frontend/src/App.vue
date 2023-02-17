<script setup>
    import NetworkGraph from './components/NetworkGraph.vue'
    import Header from './components/Header.vue'
</script>

<template>
    <Header />
    <div id="main" class="main">
        <NetworkGraph />
    </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css?family=Fira Sans');

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

#app {
    /* display: flex;
    flex-direction: column; */
    height: 100%;
    margin: 0;
    padding: 0;
}


.main {
    width: 98%;
    height: 88%;
    margin: 1%;
    margin-top: 0.1%;
    flex: 2;
}

</style>