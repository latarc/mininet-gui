<script setup>
    import NetworkGraph from './components/NetworkGraph.vue'
    // import MenuSidebar from './components/MenuSidebar.vue'
</script>

<template>
    <header>
        <div class="header-menu">
            <button>File</button>
            <button>Edit</button>
            <button>View</button>
            <button>Run</button>
        </div>
        <p class="header-logo">Mininet-GUI</p>
    </header>
    <NetworkGraph class="network-graph" />
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
    background-color: #101d42ff;
}

#app {
    display: flex;
    flex-direction: column;
    height: 100%;
}

header {
    position: relative;
    flex: 1;
    background-color: #0d1317ff;
    /* width: 95%; */
    /* height: fit-content; */
    margin: 1%;
    height: 13%;
    border-radius: 5px;
    /* padding: 10px; */
}

.header-menu {
    position: absolute;
    bottom: 0;
}

.header-menu button {
    font-size: 12pt;
    font-family: Fira Sans;
    margin: 5pt;
    padding: 3pt 5pt 3pt 5pt;
    border: none;
    background-color: #0d1317ff;
    color: white;
    width: fit-content;
    height: fit-content;
}

.header-menu button:active {
    background-color: #232ed1ff;
    border-radius: 5px 5px 5px 5px;
    /* color: black; */
}

.header-logo {
    user-select: none;
    font-size: 16pt;
    font-family: monospace;
    margin: 10pt;
    margin-right: 20pt;
    border-radius: 0px 15px 0px 30px;
    padding: 8pt;
    float: right;
    background-color: #232ed1ff;
    color: black;
    width: fit-content;
    height: fit-content;
}


.network-graph {
    /* margin-top:auto; */
    /* position: relative; */
    background-color: #89d2dcff;
    height: 82%;
    margin: 1%;
    margin-top: 0.1%;
    border-radius: 5px;
}

</style>