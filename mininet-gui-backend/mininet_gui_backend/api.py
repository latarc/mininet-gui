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
from mininet.clean import cleanup as mn_cleanup
from mininet.node import RemoteController, Controller
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from export import export_net_to_script
from cli import CLISession


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

controllers = dict(
    c0=Controller(
        id="c0",
        type="controller",
        name="c0",
        label="default controller",
        x=0,
        y=0,
        remote=False,
        ip="127.0.0.1",
    )
)
switches = dict()
hosts = dict()
links = set()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://192.168.1.83:8000",
    "http://192.168.1.83:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#mn_cleanup()

# Create the Mininet network
setLogLevel("debug")
net = Mininet(topo=Topo())
#net.addController()
net_is_started = False


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


@app.get("/api/mininet/links")
def list_edges():
    return list(links)

@app.get("/api/mininet/start")
def get_network_started():
    return net_is_started

@app.post("/api/mininet/start")
def start_network():
    """Build network and start nodes"""
    global net_is_started
    if net_is_started:
        raise HTTPException(status_code=400, detail="network already started")
    net.build()
    for controller in controllers:
        net.nameToNode[controller].start()
    for switch in switches:
        net.nameToNode[switch].start([net.nameToNode[switches[switch]["controller"]]])
    net_is_started = True
    return {"status": "ok"}

@app.post("/api/mininet/pingall")
def run_pingall():
    """Build network and start nodes"""
    global net_is_started
    if not net_is_started:
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
    hosts[host.name] = host.dict()
    debug(new_host)
    # new_host.setMAC(host.mac)
    # Return an OK status code
    return {"status": "ok"}


@app.post("/api/mininet/switches")
def create_switch(switch: Switch):
    # Create switch in the Mininet network using the request data
    if switch.controller not in controllers:
        raise HTTPException(
            status_code=400, detail=f'controller "{switch.controller}" does not exist'
        )
    new_switch = net.addSwitch(switch.name, ports=switch.ports)
    if net_is_started:
        new_switch.start([net.nameToNode[switch.controller]])
    switches[switch.name] = switch.dict()
    # Return an OK status code
    return {"status": "ok"}


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


@app.post("/api/mininet/links")
def create_link(link: Tuple[str, str]):
    # Create the link in the Mininet network using the link data
    net.addLink(link[0], link[1])
    links.add(link)
    # Return an OK status code
    return {"status": "ok"}


# @app.post("/api/mininet/cli")
# def create_cli(session: int):
#    cli_sessions[session] = CLISession()
#    url = cli_sessions[session].url
#    return {"socket_url": url}
