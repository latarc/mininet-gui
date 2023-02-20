"""
Mininet-GUI API to deploy and manage a mininet network instance.

## Deploy

Endpoints to start and stop the network at any point.

## Topology

Endpoints that add, remove and edit nodes and edges in real time.
"""
from typing import Tuple

from mininet.net import Mininet
from mininet.log import setLogLevel, info, debug
from mininet.topo import Topo, MinimalTopo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mininet_gui_backend.export import export_net_to_script
from mininet_gui_backend.cli import CLISession


class Node(BaseModel):
    id: int
    type: str
    name: str
    label: str
    x: int
    y: int


class Controller(Node):
    remote: bool
    ip: str


class Host(Node):
    ip: str
    mac: str

class Switch(Node):
    ports: int
    controller: str

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

cli_sessions = dict()

controllers = dict()
switches = dict()
hosts = dict()
links = set()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
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

# Create the Mininet network
setLogLevel("debug")
net = Mininet(topo=Topo())
net.started = False

@app.post("/api/mininet/start")
def start_network():
    """Build network and start nodes"""
    if net.started is True:
        raise HTTPException(status_code=400, detail="network already started")
    net.build()
    for switch in switches:
        switch = net.nameToNode[switch]
        switch.start([switches[switch].controller])
    net.started = True
    return {"status": "ok"}

@app.get("/api/mininet/export")
def export_network():
    debug(net)
    return {"script": export_net_to_script(net)}

@app.get("/api/mininet/hosts")
def list_hosts():
    return hosts

@app.get("/api/mininet/switches")
def list_switches():
    return switches

@app.get("/api/mininet/nodes")
def list_nodes():
    return list(hosts.values()) + list(switches.values())

@app.get("/api/mininet/links")
def list_edges():
    return list(net.links)

@app.post("/api/mininet/host")
def create_host(host: Host):
    # Create host in the Mininet network using the request data
    debug(host)
    new_host = net.addHost(host.name, ip=host.ip)
    new_host.x = host.x
    new_host.y = host.y
    hosts[host.name] = host.dict()
    debug(new_host)
    # new_host.setMAC(host.mac)
    # Return an OK status code
    return {"status": "ok"}

@app.post("/api/mininet/switch")
def create_switch(switch: Switch):
    # Create switch in the Mininet network using the request data
    new_switch = net.addSwitch(switch.name, ports=switch.ports)
    if net.started is True:
        new_switch.start([controllers[switch.controller]])
    switches[switch.name] = switch.dict()
    # Return an OK status code
    return {"status": "ok"}

@app.post("/api/mininet/controller")
def create_controller(controller: Controller):
    # Create controller in the Mininet network using the request data
    debug(controller)
    new_controller = net.addController(controller.name, ip=controller.ip, x=controller.x)
    new_controller.x = controller.x
    new_controller.y = controller.y
    controllers[controller.name] = controller.dict()
    debug(new_controller)
    # Return an OK status code
    return {"status": "ok"}

@app.post("/api/mininet/links")
def create_link(link: Tuple[str, str]):
    # Create the link in the Mininet network using the link data
    net.addLink(link[0], link[1])
    links.add(link)
    # Return an OK status code
    return {"status": "ok"}

@app.post("api/mininet/cli")
def create_cli(session: int):
    cli_sessions[session] = CLISession()
    url = cli_sessions[session].url
    return {"socket_url": url}