"""
Mininet-GUI API to deploy and manage a mininet network instance.

## Deploy

Endpoints to start and stop the network at any point.

## Topology

Endpoints that add, remove and edit nodes and edges in real time.
"""
import os
import pty
import json
import select
import asyncio
from typing import Tuple, Union
from contextlib import asynccontextmanager

from mininet.net import Mininet
from mininet.log import setLogLevel, info, debug as _debug
from mininet.topo import Topo, MinimalTopo
from mininet.clean import cleanup as mn_cleanup
from mininet.node import RemoteController, Controller as ReferenceController
from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from mininet_gui_backend.export import export_net_to_script, export_net_to_json
from mininet_gui_backend.cli import CLISession
from mininet_gui_backend.schema import Switch, Host, Controller


FLOW_FIELDS = [
    "cookie", "duration", "table", "n_packets", "n_bytes", 
    "idle_timeout", "priority", "actions"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # start
    mn_cleanup()
    app.controllers = dict()
    app.switches = dict()
    app.hosts = dict()
    app.links = dict()
    app.terminals = dict()
    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    app.net.is_started = False
    start_network()
    app.net.is_started = True
    yield
    # stop
    mn_cleanup()

app = FastAPI(
    debug=True,
    lifespan=lifespan,
    title="Mininet-GUI-API",
    description=__doc__,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Lucas Schneider",
        "url": "https://github.com/schneider8357",
        "email": "schneider8357@hotmail.com",
    },
    # license_info={
    #     "name": "Apache 2.0",
    #     "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    # },
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def debug(msg, *args):
    _debug(str(msg)+" "+" ".join(map(str, args))+"\n")

@app.get("/api/mininet/hosts")
def list_hosts():
    return app.hosts

@app.get("/api/mininet/switches")
def list_switches():
    return app.switches

@app.get("/api/mininet/controllers")
def list_controllers():
    return app.controllers

@app.get("/api/mininet/links")
def list_edges():
    return [e for e in app.links]

@app.get("/api/mininet/start")
def get_network_started():
    return app.net.is_started

@app.post("/api/mininet/start")
def start_network():
    """Build network and start nodes"""
    if app.net.is_started:
        raise HTTPException(status_code=400, detail="network already started")
    app.net.build()
    for controller in app.controllers:
        app.net.nameToNode[controller].start()
    for switch_id in app.switches:
        switch = app.net.nameToNode[switch_id]
        if switch.controller:
            switch.start([switch.controller])
        else:
            switch.start([])
    app.net.is_started = True
    return {"status": "ok"}

@app.post("/api/mininet/stop")
def stop_network():
    """Stop network and nodes"""
    # delete mininet
    try: del app.net
    except AttributeError: pass

    # Cleanup (mn -c)
    mn_cleanup()

    app.controllers.clear()
    app.switches.clear()
    app.hosts.clear()
    app.links.clear()

    # Create the Mininet network
    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    #app.net.addController()
    app.net.is_started = False
    return {"status": "ok"}

@app.post("/api/mininet/reset")
def reset_network():
    """Restart network and nodes"""
    stop_network()
    return start_network()

@app.post("/api/mininet/pingall")
def run_pingall():
    """Build network and start nodes"""
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to run pingall")
    pingall_results = app.net.pingFull()
    debug(pingall_results)
    return "\n".join([f"{p[0]}->{p[1]}: {p[2][0]}/{p[2][1]}, rtt min/avg/max/mdev {p[2][2]:.3f}/{p[2][3]:.3f}/{p[2][4]:.3f}/{p[2][5]:.3f} ms" for p in pingall_results])

@app.post("/api/mininet/hosts")
def create_host(host: Host):
    if host.id in app.hosts:
        app.hosts[host.id] = host
        return {"status": "updated"}
    # Create host in the Mininet network using the request data
    debug(host)
    new_host = app.net.addHost(host.name, ip=host.ip)
    new_host.x = host.x
    new_host.y = host.y
    new_host.ip = host.ip
    new_host.type = "host"
    app.hosts[host.name] = host
    debug(new_host)
    # Return an OK status code
    return {"status": "ok"}


@app.post("/api/mininet/switches")
def create_switch(switch: Switch):
    # Create switch in the Mininet network using the request data
    debug("CREATING SWITCH", switch)
    if switch.controller and switch.controller not in app.controllers:
        raise HTTPException(
            status_code=400, detail=f'controller "{switch.controller}" does not exist'
        )
    new_switch = app.net.addSwitch(switch.name, ports=switch.ports)
    if app.net.is_started and switch.controller:
        new_switch.start([app.net.nameToNode[switch.controller]])
    else:
        new_switch.start([])
    new_switch.x = switch.x
    new_switch.y = switch.y
    new_switch.type = "sw"
    new_switch.controller = switch.controller
    app.switches[switch.name] = switch
    return switch


@app.post("/api/mininet/controllers")
def create_controller(controller: Controller):
    # Create controller in the Mininet network using the request data
    debug(controller)
    if controller.remote:
        # TODO aqui o mininet verifica se a porta está open com timeout de 60s e blocka a request 
        new_controller = app.net.addController(
            controller.name,
            controller=RemoteController,
            ip=controller.ip,
            port=controller.port,
        )
    else:
        new_controller = app.net.addController(
            controller.name, controller=ReferenceController
        )

    new_controller.start()
    new_controller.x = controller.x
    new_controller.y = controller.y
    new_controller.type = "controller"
    app.controllers[controller.name] = controller
    debug(new_controller)
    # Return an OK status code
    return {"status": "ok"}

@app.post("/api/mininet/associate_switch")
def associate_switch(data: dict):
    # Associate switch to controller.
    if "switch" not in data or "controller" not in data:
        raise HTTPException(
            status_code=400, detail=f'missing key in data'
        )
    sw_id = data["switch"]
    ctl_id = data["controller"]
    if sw_id not in app.net.nameToNode or ctl_id not in app.net.nameToNode:
        raise HTTPException(status_code=400, detail='node not in net')
    sw = app.net.nameToNode[sw_id]
    ctl = app.net.nameToNode[ctl_id]
    if app.switches[sw_id].controller:
        raise HTTPException(status_code=400, detail="switch is already associated")
    sw.controller = ctl
    app.switches[sw_id].controller = ctl_id
    if app.net.is_started:
        sw.start([sw.controller])
    return "OK"

@app.post("/api/mininet/links")
def create_link(link: Tuple[str, str]):
    # Create the link in the Mininet network using the link data
    if link[0] not in app.net.nameToNode or link[1] not in app.net.nameToNode:
        raise HTTPException(status_code=400, detail=f'node not in net')
    key = frozenset((link[0], link[1]))
    if key in app.links:
        raise HTTPException(status_code=400, detail=f'link already exists')
    new_link = app.net.addLink(link[0], link[1])
    if app.net.is_started:
        for node in link:
            node = app.net.nameToNode[node]
            if node.type == "host":
                node.configDefault()
            elif node.type == "sw" and node.controller:
                # Important, otherwise switch doesnt init the port
                node.start([node.controller])
    # It is important to store this Link object because
    # mininet (apparently) doesn't have an easy way to access this
    app.links[key] = new_link
    return {"from": link[0], "to": link[1]}


@app.post("/api/mininet/node_position")
def node_position(data: dict):
    if "node_id" not in data or "position" not in data:
        raise HTTPException(
            status_code=400, detail=f'missing key in data'
        )
    debug("data:",data)
    node_id = data["node_id"]
    x, y = data["position"]
    if node_id not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    node = app.net.nameToNode[node_id]
    debug("before update xy",(node.x, node.y))
    node.x = x
    node.y = y
    debug("updated xy",(app.net.nameToNode[node_id].x, app.net.nameToNode[node_id].y))
    if node.type == "sw":
        app.switches[node_id].x = x
        app.switches[node_id].y = y
    elif node.type == "host":
        app.hosts[node_id].x = x
        app.hosts[node_id].y = y
    elif node.type == "controller":
        app.controllers[node_id].x = x
        app.controllers[node_id].y = y
    return {"message": f"Node {node_id} updated successfully"}


@app.delete("/api/mininet/delete_node/{node_id}")
def delete_node(node_id: str):
    if node_id not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    node = app.net.nameToNode[node_id]
    app.net.delNode(node)
    if node.type == "sw":
        del app.switches[node_id]
    elif node.type == "host":
        del app.hosts[node_id]
    elif node.type == "controller":
        del app.controllers[node_id]
        for switch_id in app.switches:
            switch = app.switches[switch_id]
            if switch.controller == node_id:
                debug("CONTROLLER", switch.controller, node_id)
                app.switches[switch_id].controller = None
                app.net.nameToNode[switch_id].start([])
    return {"message": f"Node {node_id} deleted successfully"}

@app.delete("/api/mininet/delete_link/{src_id}/{dst_id}")
def delete_link(src_id: str, dst_id: str):
    key = frozenset((src_id, dst_id))
    if key not in app.links:
        raise HTTPException(status_code=404, detail=f"Node not found")
    app.net.delLink(app.links[key])
    del app.links[key]
    return {"message": f"Link {key} deleted successfully"}

@app.delete("/api/mininet/remove_association/{src_id}/{dst_id}")
def remove_association(src_id: str, dst_id: str):
    if src_id not in app.net.nameToNode or dst_id not in app.net.nameToNode:
        raise HTTPException(status_code=400, detail='node not in net')
    sw, ctl = None, None
    for node_id in (src_id, dst_id):
        node = app.net.nameToNode[node_id]
        if node.type == "sw":
            sw = node
        elif node.type == "controller":
            ctl = node
    if not sw or not ctl:
        raise HTTPException(status_code=400, detail=f'node {node_id} isnt switch or controller')
    sw.controller = None
    app.switches[sw.name].controller = None
    if app.net.is_started:
        sw.start([])
    return "OK"


@app.get("/api/mininet/stats/{node_id}")
def get_node_stats(node_id: str):
    if node_id not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    node = app.net.nameToNode[node_id]
    base_data = app.switches.get(node_id) or app.hosts.get(node_id) or app.controllers.get(node_id)
    if not base_data:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    result = dict(**base_data.dict())

    if node.type == "sw":
        ports_raw = node.dpctl("dump-ports")
        ports_raw = ports_raw[ports_raw.find("\n") + 1:].replace("\n", " ")
        result["ports"] = [p.strip() for p in ports_raw.split("port") if "LOCAL" not in p and p.strip()]

        flow_table_raw = node.dpctl("dump-flows").strip()
        parsed_flows = []

        for line in flow_table_raw.split("\n"):
            fields = line.split(",")
            flow = {}
            match_fields = {}

            for field in fields:
                key_val = field.strip().split("=")

                if len(key_val) == 2:
                    key, value = key_val
                    if key in FLOW_FIELDS:
                        flow[key] = value
                    else:
                        match_fields[key] = value

            flow["match_fields"] = match_fields
            parsed_flows.append(flow)
        result["flow_table"] = parsed_flows
    elif node.type == "host":
        arp_table = node.cmd("arp -a -n")
        print("ARP TABLE", arp_table)
        parsed_arp_table = []
        for line in arp_table.splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            ip = parts[1].strip("()")
            mac = parts[3]
            interface = parts[-1]
            parsed_arp_table.append({"ip": ip, "mac": mac, "interface": interface})
        result["arp_table"] = parsed_arp_table

    result.pop("x", None)
    result.pop("y", None)
    
    return result

@app.get("/api/mininet/export_script", response_class=PlainTextResponse)
def export_network():
    debug(app.net)
    return export_net_to_script(app.switches, app.hosts, app.controllers, app.links).encode("utf-8")

@app.get("/api/mininet/export_json", response_class=PlainTextResponse)
def export_network():
    debug(app.net)
    return export_net_to_json(app.switches, app.hosts, app.controllers, app.links).encode("utf-8")

@app.post("/api/mininet/import_json")
async def import_json(file: UploadFile = File(...)):
    contents = await file.read()
    
    try:
        data = json.loads(contents.decode("utf-8"))
        print("Received Topology JSON:", data)

        for controller_data in data.get("controllers", []):
            controller = Controller(**controller_data)
            create_controller(controller)

        for switch_data in data.get("switches", []):
            switch = Switch(**switch_data)
            controller = switch.controller
            switch.controller = None
            create_switch(switch)
            if controller:
                associate_switch({
                    "switch": switch.id,
                    "controller": controller
                })

        for host_data in data.get("hosts", []):
            host = Host(**host_data)
            create_host(host)

        for link in data.get("links", []):
            debug("LINKS: ", data["links"])
            debug("LINK: ", link)
            create_link(tuple(link))

        return {"message": "Topology successfully imported"}

    except json.JSONDecodeError:
        return {"error": "Invalid JSON file"}, 400

async def read_pty(master_fd, websocket: WebSocket):
    """Reads PTY output and sends it to WebSocket"""
    try:
        while True:
            await asyncio.sleep(0.01)
            r, _, _ = select.select([master_fd], [], [], 0)
            if master_fd in r:
                output = os.read(master_fd, 1024).decode(errors="ignore")
                await websocket.send_text(output)
    except Exception as e:
        debug(f"PTY Read Error: {e}")

@app.websocket("/api/mininet/terminal/{node_id}")
async def websocket_terminal(websocket: WebSocket, node_id: str):
    """WebSocket endpoint for accessing a Mininet node terminal"""
    await websocket.accept()
    
    node = app.net.get(node_id)

    if not node:
        await websocket.send_text(f"Error: node {node_id} not found.")
        await websocket.close()
        return

    master_fd, slave_fd = pty.openpty()

    process = node.popen(["/bin/bash", "-i"], stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, text=True, close_fds=True)

    app.terminals[node_id] = (master_fd, process)

    asyncio.create_task(read_pty(master_fd, websocket))

    try:
        while True:
            data = await websocket.receive_text()
            debug("RECEIVED",data.encode())
            os.write(master_fd, data.encode())
    except WebSocketDisconnect:
        process.terminate()
        os.close(master_fd)
        app.terminals.pop(node_id, None)
        print(f"Closed terminal session for {node_id}")
