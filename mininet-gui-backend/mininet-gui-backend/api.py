from typing import Dict

from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import Link
from mininet.log import setLogLevel, info, debug
from mininet.topo import Topo, MinimalTopo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

description = """
Mininet-GUI API to deploy and manage a mininet network instance.

## Deploy

Endpoints to start and stop the network at any point.

## Topology

Endpoints that add, remove and edit nodes and edges in real time.
"""


class Node(BaseModel):
    node_id: int
    node_type: str
    name: str

class Host(Node):
    ip: str
    mac: str


class Switch(Node):
    ports: int

app = FastAPI(
    debug=True,
    title="Mininet-GUI-API",
    description=description,
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
net = Mininet(controller=Controller, topo=Topo())
net.started = False
c0 = net.addController("c0")

@app.post("/api/mininet/start")
def start_network():
    """Build network and start nodes"""
    if net.started is True:
        raise HTTPException(status_code=400, detail="network already started")
    net.build()
    net.started = True
    return {"status": "ok"}

@app.get("/api/mininet/nodes")
def list_nodes():
    debug(net.nameToNode.keys())
    return {"nodes": list(net.nameToNode.keys())}

@app.get("/api/mininet/edges")
def list_edges():
    return net.topo.g.edges()

@app.post("/api/mininet/host")
def create_host(host: Host):
    # Create host in the Mininet network using the request data
    debug(host)
    new_host = net.addHost(host.name, ip=host.ip)
    # new_host.setMAC(host.mac)
    # Return an OK status code
    return {"status": "ok"}

@app.post("/api/mininet/switch")
def create_switch(switch: Switch):
    # Create switch in the Mininet network using the request data
    new_switch = net.addSwitch(switch.name, ports=switch.ports)
    new_switch.start([])
    # Return an OK status code
    return {"status": "ok"}

#@app.post("/api/mininet/links")
#def create_link(link: Dict[str, Any]):
#    # Create the link in the Mininet network using the link data
#    net.addLink(link["node1"], link["node2"])
#    # Return an OK status code
#    return {"status": "ok"}

