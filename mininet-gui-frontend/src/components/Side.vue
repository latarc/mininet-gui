
<template>
    <div id="side" class="side">
            <p>Mininet Controls</p>
            <button id="button-start-network" class="button-control-network">Start Network</button>
            <button id="button-create-link" class="button-control-network">Create Link</button>
            <button id="button-export-network" class="button-control-network">Export Network</button>
    </div>
    <button id="button-hide-side" class="button-hide-side" @click="toggleSide()" ><b>&lt;&lt;</b></button>
</template>

<script>
export default {
  props: {
    side: 1
  },
  methods: {
    toggleSide() {
        if (side) {
            side = 0
            document.getElementById("side").style.display = "none";
            document.getElementById("button-hide-side").style.marginLeft = 0;
        } else {
            side = 1
            document.getElementById("side").style.display = "block";
            document.getElementById("button-hide-side").style.marginLeft = "180px";
        }
    }
  }
};
</script>

<style>

.side {
    background: rgba(0, 0, 0, .8);
    height: inherit;
    width: 180px;
    position: absolute;
    z-index: 2;
    /* margin: 1%; */
    margin-top: 0%;
    border-radius: 4px 0 0 4px;
    overflow-x: hidden;
    overflow-y: auto;

}

.side * {
    color: white;
    font-family: Fira Sans;
    margin: 2.5%;
    padding: 4px;

}

.button-control-network {
    background: var(--oxford-blue);
    border: solid 2px rgba(0, 0, 0, .2);
    border-radius: 2px;
    font-size: 11pt;
}

.button-control-network:active {
    background: var(--slate-blue);
}

.button-hide-side {
    position: absolute;
    z-index: 4;
    padding: 0;
    margin-left: 180px;
    height: inherit;
    width: 12px;
    font-size: 8pt;
    border: none;
    border-radius: 0 9px 9px 0;
    background: rgba(0, 0, 0, .9);
    color: white;
}


</style>