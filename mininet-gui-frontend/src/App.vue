<script setup>
    import NetworkGraph from './components/NetworkGraph.vue'
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
    <div id="main" class="main">
        <div id="side" class="side">
            <p>Mininet Controls</p>
            <button id="button-start-network" class="button-start-network">Start Network</button>
            <button id="button-hide-side" class="button-hide-side" ><b>&lt;&lt;</b></button>
        </div>
        <NetworkGraph class="network-graph" />
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
    background-color: #101d42ff;
}

#app {
    /* display: flex;
    flex-direction: column; */
    height: 100%;
}

header {
    position: relative;
    flex: 1;
    background-color: #0d1317ff;
    /* width: 95%; */
    /* height: fit-content; */
    margin: 0.5%;
    height: 10%;
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
    font-size: 13pt;
    font-family: monospace;
    margin: 1%;
    margin-right: 2%;
    border-radius: 0px 15px 0px 30px;
    padding: 8pt;
    float: right;
    background-color: #232ed1ff;
    color: black;
    width: fit-content;
    height: fit-content;
}

.main {
    width: 98%;
    height: 87%;
    margin: 1%;
    margin-top: 0.1%;
    flex: 2;
}

.side {
    background: rgba(0, 0, 0, .8);
    height: inherit;
    width: 180px;
    position: absolute;
    z-index: 2;
    /* margin: 1%; */
    margin-top: 0%;
    border-radius: 4px;

}

.side * {
    font-family: Fira Sans;

}

.button-start-network {
    background: #6564dbff;
    border: solid 2px rgba(0, 0, 0, .2);
    border-radius: 2px;
    font-size: 11pt;
    margin: 6%;
    padding: 4px;
}

.button-hide-side {
    position: absolute;
    z-index: 2;
    right: 0%;
    top: 0;
    padding: 0;
    height: 100%;
    width: 12px;
    font-size: 8pt;
    border: none;
    background: rgba(0, 0, 0, .2);
    color: white;
}

.network-graph {
    /* margin-top:auto; */
    /* position: relative; */
    background-color: #89d2dcff;
    height: inherit;
    width: inherit;
    border-radius: 5px;
    position: absolute;
    z-index: 1;
}

</style>