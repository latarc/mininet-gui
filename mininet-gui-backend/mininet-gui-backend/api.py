from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import Link
from mininet.log import setLogLevel, info, debug
from typing import Dict
from pydantic import BaseModel


class Node(BaseModel):
    node_id: int
    node_type: str
    name: str
    ip: str
    mac: str


app = FastAPI(debug=True)

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
net = Mininet(controller=Controller)
c0 = net.addController("c0")
net.build()

@app.post("/api/nodes")
def create_node(node: Node):
    # Create the node in the Mininet network using the node data
    debug(node)
    if node.node_type == "host":
        net.addHost(node.name, ip=node.ip, mac=node.mac)
    elif node.node_type == "switch":
        switch = net.addSwitch(node.name)
        switch.start([])
    # h4.setMAC("000000000140")
    # Return an OK status code
    return {"status": "ok"}

#@app.post("/api/links")
#def create_link(link: Dict[str, Any]):
#    # Create the link in the Mininet network using the link data
#    net.addLink(link["node1"], link["node2"])
#    # Return an OK status code
#    return {"status": "ok"}

