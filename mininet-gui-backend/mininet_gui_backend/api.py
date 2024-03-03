"""
Mininet-GUI API to deploy and manage a mininet network instance.

## Deploy

Endpoints to start and stop the network at any point.

## Topology

Endpoints that add, remove and edit nodes and edges in real time.
"""
from typing import Tuple, Union

from mininet.net import Mininet
from mininet.log import setLogLevel, info, debug
from mininet.topo import Topo, MinimalTopo
from mininet.clean import cleanup as mn_cleanup
from mininet.node import RemoteController, Controller
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from mininet_gui_backend.export import export_net_to_script
from mininet_gui_backend.cli import CLISession


class Node(BaseModel):
    id: str
    type: str
    name: str
    label: str
    x: float
    y: float


class Controller(Node):
    remote: bool
    ip: str


class Host(Node):
    ip: str
    mac: str


class Switch(Node):
    ports: int
    controller: Union[str, None]


app = FastAPI(
    debug=True,
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

controllers = dict()
switches = dict()
hosts = dict()
links = dict()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cleanup (mn -c)
mn_cleanup()

# Create the Mininet network
setLogLevel("debug")
net = Mininet(autoSetMacs=True, topo=Topo())
#net.addController()
net.is_started = False


@app.get("/api/mininet/export", response_class=PlainTextResponse)
def export_network():
    debug(net)
    return export_net_to_script(net).encode("utf-8")


@app.get("/api/mininet/hosts")
def list_hosts():
    return hosts


@app.get("/api/mininet/switches")
def list_switches():
    return switches

@app.get("/api/mininet/controllers")
def list_controllers():
    return controllers

@app.get("/api/mininet/links")
def list_edges():
    return [e["tuple"] for e in links.values()]

@app.get("/api/mininet/start")
def get_network_started():
    return net.is_started

@app.post("/api/mininet/start")
def start_network():
    """Build network and start nodes"""
    if net.is_started:
        raise HTTPException(status_code=400, detail="network already started")
    net.build()
    for controller in controllers:
        net.nameToNode[controller].start()
    for switch_id in switches:
        switch = net.nameToNode[switch_id]
        if switch.controller:
            switch.start([switch.controller])
        else:
            new_switch.start([])
    net.is_started = True
    return {"status": "ok"}

@app.post("/api/mininet/pingall")
def run_pingall():
    """Build network and start nodes"""
    if not net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to run pingall")
    pingall_results = net.pingFull()
    debug(pingall_results)
    return "\n".join([f"{p[0]}->{p[1]}: {p[2][0]}/{p[2][1]}, rtt min/avg/max/mdev {p[2][2]:.3f}/{p[2][3]:.3f}/{p[2][4]:.3f}/{p[2][5]:.3f} ms" for p in pingall_results])

@app.post("/api/mininet/hosts")
def create_host(host: Host):
    if host.id in hosts:
        hosts[host.id] = host
        return {"status": "updated"}
    # Create host in the Mininet network using the request data
    debug(host)
    new_host = net.addHost(host.name, ip=host.ip)
    new_host.x = host.x
    new_host.y = host.y
    new_host.type = "host"
    hosts[host.name] = host.dict()
    debug(new_host)
    # Return an OK status code
    return {"status": "ok"}


@app.post("/api/mininet/switches")
def create_switch(switch: Switch):
    # Create switch in the Mininet network using the request data
    debug("CREATING SWITCH", switch)
    if switch.controller and switch.controller not in controllers:
        raise HTTPException(
            status_code=400, detail=f'controller "{switch.controller}" does not exist'
        )
    new_switch = net.addSwitch(switch.name, ports=switch.ports)
    if net.is_started and switch.controller:
        new_switch.start([net.nameToNode[switch.controller]])
    else:
        new_switch.start([])
    new_switch.type = "sw"
    new_switch.controller = switch.controller
    switches[switch.name] = switch.dict()
    return switch


@app.post("/api/mininet/controllers")
def create_controller(controller: Controller):
    # Create controller in the Mininet network using the request data
    debug(controller)
    if controller.remote:
        new_controller = net.addController(
            controller.name, controller=RemoteController, ip=controller.ip
        )
    else:
        new_controller = net.addController(
            controller.name, controller=Controller
        )

    new_controller.start()
    new_controller.x = controller.x
    new_controller.y = controller.y
    controllers[controller.name] = controller.dict()
    debug(new_controller)
    # Return an OK status code
    return {"status": "ok"}

@app.post("/api/mininet/associate")
def associate_switch(data: dict):
    # Associate switch to controller.
    if "switch" not in data or "controller" not in data:
        raise HTTPException(
            status_code=400, detail=f'missing key in data'
        )
    sw_id = data["switch"]
    ctl_id = data["controller"]
    if sw_id not in net.nameToNode or ctl_id not in net.nameToNode:
        raise HTTPException(status_code=400, detail='node not in net')
    sw = net.nameToNode[sw_id]
    ctl = net.nameToNode[ctl_id]
    if sw.controller:
        raise HTTPException(status_code=400, detail="switch is already associated")
    sw.controller = ctl
    switches[sw_id]["controller"] = ctl_id
    if net.is_started:
        sw.start([sw.controller])
    return "OK"

@app.post("/api/mininet/links")
def create_link(link: Tuple[str, str]):
    # Create the link in the Mininet network using the link data
    if link[0] not in net.nameToNode or link[1] not in net.nameToNode:
        raise HTTPException(status_code=400, detail=f'node not in net')
    new_link = net.addLink(link[0], link[1])
    if net.is_started:
        for node in link:
            node = net.nameToNode[node]
            if node.type == "host":
                node.configDefault()
            elif node.type == "sw":
                node.start([net.nameToNode[node.controller]])
    link_name = f"{new_link.intf1.name}_{new_link.intf2.name}"
    # It is important to store this Link object because
    # mininet (apparently) doesn't have an easy way to access this
    links[link_name] = {"tuple": link, "object": new_link}
    return {"from": link[0], "to": link[1], "id": link_name}

@app.delete("/api/mininet/delete_node/{node_id}")
def delete_node(node_id: str):
    if node_id not in net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    node = net.nameToNode[node_id]
    net.delNode(node)
    if node.type == "sw":
        del switches[node_id]
    elif node.type == "host":
        del hosts[node_id]
    return {"message": f"Node {node_id} deleted successfully"}

@app.delete("/api/mininet/delete_link/{link_id}")
def delete_link(link_id: str):
    if link_id not in links:
        raise HTTPException(status_code=404, detail=f"Node not found")
    net.delLink(links[link_id]["object"])
    del links[link_id]
    return {"message": f"Link {link_id} deleted successfully"}

@app.get("/api/mininet/stats/{node_id}")
def get_node_stats(node_id: str):
    if node_id not in net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    node = net.nameToNode[node_id]
    result = dict(**(switches.get(node_id) or hosts.get(node_id)))
    if node.type == "sw":
        ports = node.dpctl("dump-ports")
        ports = ports[ports.find("\n")+1:].replace("\n", " ")
        ports = [p for p in ports.split("port") if "LOCAL" not in p]
        result["ports"] = [p for p in ports if p.strip()]
    return result
