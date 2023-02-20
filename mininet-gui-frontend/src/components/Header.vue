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
</template>

<style>

header {
    position: absolute;
    background-color: #0d1317ff;
    width: 95%;
    /* height: fit-content; */
    margin: 0.5%;
    margin-top: 0%;
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
    background-color: var(--slate-blue);
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
    background-color: var(--slate-blue);
    color: black;
    width: fit-content;
    height: fit-content;
}
</style>