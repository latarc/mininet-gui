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
import subprocess
import logging
import re
import uuid
from datetime import datetime
from mininet_gui_backend.sniffer import SnifferManager
import pyshark.ek_field_mapping as ek_field_mapping
from pyshark.tshark.output_parser.tshark_ek import TsharkEkJsonParser
from typing import Tuple, Union, Optional
from contextlib import asynccontextmanager
import pkgutil

from mininet.moduledeps import pathCheck

from mininet.net import Mininet
from mininet.log import setLogLevel, info, debug as _debug
from mininet.topo import Topo, MinimalTopo
from mininet.clean import cleanup as mn_cleanup
from mininet.node import RemoteController, Controller as ReferenceController, NOX, UserSwitch, OVSSwitch, OVSKernelSwitch, OVSBridge, Node
from mininet_gui_backend.nodes import Ryu
from mininet.link import TCLink
from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response

from mininet_gui_backend.export import export_net_to_script, export_net_to_json
from mininet_gui_backend.cli import CLISession
from mininet_gui_backend.schema import Switch, Host, Controller, Nat, Router
from mininet_gui_backend.flow_rules import FlowRuleCreate, FlowRuleDelete, build_flow, build_flow_match

LOG_FILE = os.path.join(os.path.dirname(__file__), "mininet.log")
RYU_APP_DIRS = []

FLOW_FIELDS = [
    "cookie", "duration", "table", "n_packets", "n_bytes", 
    "idle_timeout", "priority", "actions"
]

class LinkOptions(BaseModel):
    bw: Optional[float] = Field(None, ge=0)
    delay: Optional[Union[str, float]] = None
    jitter: Optional[Union[str, float]] = None
    loss: Optional[float] = Field(None, ge=0, le=100)
    max_queue_size: Optional[int] = Field(None, ge=0)
    use_htb: Optional[bool] = None

class LinkCreate(BaseModel):
    src: str
    dst: str
    options: Optional[LinkOptions] = None


class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()

class HostUpdate(BaseModel):
    ip: Optional[str] = None
    intf: Optional[str] = None
    default_route: Optional[str] = None
    default_route_type: Optional[str] = None
    default_route_dev: Optional[str] = None
    default_route_ip: Optional[str] = None

class IperfRequest(BaseModel):
    client: str
    server: str
    l4_type: Optional[str] = "TCP"
    udp_bw: Optional[str] = None
    fmt: Optional[str] = None
    seconds: Optional[int] = 5
    port: Optional[int] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # start
    mn_cleanup()
    setup_log_file()
    app.controllers = dict()
    app.switches = dict()
    app.hosts = dict()
    app.nats = dict()
    app.routers = dict()
    app.links = dict()
    app.link_attrs = dict()
    app.terminals = dict()
    app.sniffers = dict()
    app.sniffer_manager = SnifferManager(list_mininet_interfaces, start_sniffer_process)
    app.pingall_running = False
    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    app.net.is_started = False
    start_network()
    app.net.is_started = True
    yield
    # stop
    mn_cleanup()

from mininet_gui_backend import __version__ as BACKEND_VERSION
try:
    from mininet.net import VERSION as MININET_VERSION
except Exception:
    MININET_VERSION = None

app = FastAPI(
    debug=True,
    lifespan=lifespan,
    title="Mininet-GUI-API",
    description=__doc__,
    version=BACKEND_VERSION,
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

@app.get("/api/version")
def get_version():
    return {"version": app.version, "mininet_version": MININET_VERSION}

@app.get("/api/ryu/apps")
def get_ryu_apps():
    return {"apps": list_ryu_apps()}

def debug(msg, *args):
    _debug(str(msg)+" "+" ".join(map(str, args))+"\n")

def list_ryu_apps():
    apps = set()
    app_dirs = []
    for app_dir in RYU_APP_DIRS:
        if os.path.isdir(app_dir):
            app_dirs.append(app_dir)
    try:
        import ryu
        app_pkg = getattr(ryu, "app", None)
        if app_pkg and hasattr(app_pkg, "__path__"):
            for _finder, name, _ispkg in pkgutil.iter_modules(app_pkg.__path__):
                if name and not name.startswith("__"):
                    apps.add(name)
            pkg_dir = os.path.dirname(app_pkg.__file__)
            if os.path.isdir(pkg_dir):
                app_dirs.append(pkg_dir)
    except Exception:
        pass

    for app_dir in app_dirs:
        try:
            entries = os.listdir(app_dir)
        except OSError:
            continue
        for entry in entries:
            if entry.endswith(".py") and entry != "__init__.py":
                apps.add(entry[:-3])

    return sorted(apps)

def setup_log_file():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == handler.baseFilename for h in root_logger.handlers):
        root_logger.addHandler(handler)
    try:
        from mininet.log import lg
        lg.setLevel(logging.DEBUG)
        if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == handler.baseFilename for h in lg.handlers):
            lg.addHandler(handler)
    except Exception:
        pass

def clear_log_file():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8"):
        pass

def list_mininet_interfaces():
    nodes = []
    if hasattr(app.net, "hosts"):
        for host in app.net.hosts:
            intfs = [i.name for i in host.intfList() if i.name and i.name not in ("lo", "lo0")]
            node_type = getattr(host, "type", "host")
            nodes.append({"id": host.name, "type": node_type, "intfs": intfs, "pid": host.pid})
    if hasattr(app.net, "switches"):
        for sw in app.net.switches:
            intfs = [i.name for i in sw.intfList() if i.name and i.name not in ("lo", "lo0")]
            node_type = getattr(sw, "type", "switch")
            nodes.append({"id": sw.name, "type": node_type, "intfs": intfs, "pid": sw.pid})
    return nodes

def _parse_ip_addrs(output: str):
    addrs = []
    for line in output.splitlines():
        match = re.search(r"\sinet6?\s+([0-9a-fA-F:.]+/\d+)", line)
        if match:
            addrs.append(match.group(1))
    return addrs

@app.get("/api/mininet/addressing_plan")
def addressing_plan():
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started")
    nodes = []
    for node_id, node in app.net.nameToNode.items():
        if not getattr(node, "type", None):
            continue
        intfs = []
        for intf in node.intfList():
            if not intf.name or intf.name in ("lo", "lo0"):
                continue
            ipv4 = _parse_ip_addrs(node.cmd(f"ip -o -4 addr show {intf.name}"))
            ipv6 = _parse_ip_addrs(node.cmd(f"ip -o -6 addr show {intf.name}"))
            mac = None
            try:
                mac = intf.MAC()
            except Exception:
                pass
            intfs.append({
                "name": intf.name,
                "mac": mac,
                "ipv4": ipv4,
                "ipv6": ipv6,
            })
        nodes.append({
            "id": node_id,
            "type": node.type,
            "intfs": intfs,
        })
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "nodes": nodes,
    }

@app.get("/api/mininet/hosts")
def list_hosts():
    return app.hosts

@app.get("/api/mininet/interfaces")
def list_interfaces():
    return {"nodes": list_mininet_interfaces()}

@app.get("/api/mininet/switches")
def list_switches():
    for sw_id, sw in app.switches.items():
        if not getattr(sw, "switch_type", None):
            node = app.net.nameToNode.get(sw_id)
            if node:
                if isinstance(node, UserSwitch):
                    sw.switch_type = "user"
                elif isinstance(node, OVSBridge):
                    sw.switch_type = "ovsbridge"
                elif isinstance(node, OVSSwitch):
                    sw.switch_type = "ovs"
                elif isinstance(node, OVSKernelSwitch):
                    sw.switch_type = "ovskernel"
    return app.switches

@app.get("/api/mininet/controllers")
def list_controllers():
    return app.controllers

@app.get("/api/mininet/nats")
def list_nats():
    return app.nats

@app.get("/api/mininet/routers")
def list_routers():
    return app.routers

@app.get("/api/mininet/links")
def list_edges():
    edges = []
    for key in app.links:
        nodes = list(key)
        attrs = app.link_attrs.get(key) or {}
        if len(nodes) == 2:
            edges.append({"from": nodes[0], "to": nodes[1], "options": attrs})
    return edges

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
    app.nats.clear()
    app.routers.clear()
    app.links.clear()
    app.link_attrs.clear()

    # Create the Mininet network
    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    #app.net.addController()
    app.net.is_started = False
    return {"status": "ok"}

@app.post("/api/mininet/reset")
async def reset_network():
    """Restart network and nodes"""
    try:
        await app.sniffer_manager.stop()
    except Exception:
        pass
    clear_log_file()
    stop_network()
    return start_network()

@app.post("/api/mininet/pingall")
def run_pingall():
    """Build network and start nodes"""
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to run pingall")
    if app.pingall_running:
        raise HTTPException(status_code=409, detail="pingall already running")
    app.pingall_running = True
    try:
        pingall_results = app.net.pingFull()
        debug(pingall_results)
        return "\n".join(
            [
                f"{p[0]}->{p[1]}: {p[2][0]}/{p[2][1]}, rtt min/avg/max/mdev {p[2][2]:.3f}/{p[2][3]:.3f}/{p[2][4]:.3f}/{p[2][5]:.3f} ms"
                for p in pingall_results
            ]
        )
    finally:
        app.pingall_running = False

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

@app.post("/api/mininet/routers")
def create_router(router: Router):
    if router.id in app.routers:
        app.routers[router.id] = router
        return {"status": "updated"}
    debug(router)
    params = {"ip": router.ip, "mac": router.mac}
    new_router = app.net.addHost(router.name, cls=LinuxRouter, **params)
    new_router.x = router.x
    new_router.y = router.y
    new_router.ip = router.ip
    new_router.mac = router.mac
    new_router.type = "router"
    app.routers[router.name] = router
    debug(new_router)
    return {"status": "ok"}

@app.patch("/api/mininet/hosts/{host_id}")
def update_host(host_id: str, payload: HostUpdate):
    if host_id not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Node {host_id} not found")
    node = app.net.nameToNode[host_id]
    if getattr(node, "type", None) != "host":
        raise HTTPException(status_code=400, detail="node is not a host")
    host = app.hosts.get(host_id)
    if not host:
        raise HTTPException(status_code=404, detail=f"Host {host_id} not found")
    if payload.ip:
        ip_value = payload.ip.strip()
        if "/" in ip_value:
            addr, prefix_raw = ip_value.split("/", 1)
            try:
                prefix_len = int(prefix_raw)
            except ValueError:
                raise HTTPException(status_code=400, detail="invalid prefix length")
        else:
            addr = ip_value
            prefix_len = None
        if prefix_len is None:
            fallback = host.ip
            if fallback and "/" in fallback:
                prefix_len = int(fallback.split("/", 1)[1])
            else:
                prefix_len = 8
        intf = payload.intf or None
        node.setIP(addr, prefixLen=prefix_len, intf=intf)
        host.ip = f"{addr}/{prefix_len}"
    if payload.default_route_type:
        route_type = payload.default_route_type.strip().lower()
        if route_type == "dev":
            dev = (payload.default_route_dev or "").strip()
            if dev:
                node.setDefaultRoute(dev)
            else:
                node.cmd("ip route del default")
        elif route_type == "ip":
            ip_value = (payload.default_route_ip or "").strip()
            if ip_value:
                node.setDefaultRoute(f"via {ip_value}")
            else:
                node.cmd("ip route del default")
    elif payload.default_route is not None:
        route_value = payload.default_route.strip()
        if route_value:
            node.setDefaultRoute(route_value)
        else:
            node.cmd("ip route del default")
    app.hosts[host_id] = host
    return {"status": "ok", "host": host.model_dump()}

@app.post("/api/mininet/nats")
def create_nat(nat: Nat):
    if nat.id in app.nats:
        app.nats[nat.id] = nat
        return {"status": "updated"}
    debug(nat)
    params = {}
    if nat.ip:
        params["ip"] = nat.ip
    if nat.mac:
        params["mac"] = nat.mac
    new_nat = app.net.addNAT(nat.name, connect=False, **params)
    new_nat.x = nat.x
    new_nat.y = nat.y
    new_nat.type = "nat"
    if nat.ip:
        new_nat.ip = nat.ip
    if nat.mac:
        new_nat.mac = nat.mac
    app.nats[nat.name] = nat
    debug(new_nat)
    return {"status": "ok"}


@app.post("/api/mininet/switches")
def create_switch(switch: Switch):
    # Create switch in the Mininet network using the request data
    debug("CREATING SWITCH", switch)
    if switch.controller and switch.controller not in app.controllers:
        raise HTTPException(
            status_code=400, detail=f'controller "{switch.controller}" does not exist'
        )
    switch_type = (switch.switch_type or "").lower()
    switch.switch_type = switch_type or switch.switch_type
    if switch_type == "user":
        new_switch = app.net.addSwitch(switch.name, ports=switch.ports, cls=UserSwitch)
    elif switch_type == "ovs":
        new_switch = app.net.addSwitch(switch.name, ports=switch.ports, cls=OVSSwitch)
    elif switch_type == "ovskernel":
        new_switch = app.net.addSwitch(switch.name, ports=switch.ports, cls=OVSKernelSwitch)
    elif switch_type == "ovsbridge":
        new_switch = app.net.addSwitch(switch.name, ports=switch.ports, cls=OVSBridge)
    else:
        new_switch = app.net.addSwitch(switch.name, ports=switch.ports)
    if app.net.is_started and switch.controller:
        new_switch.start([app.net.nameToNode[switch.controller]])
    else:
        new_switch.start([])
    new_switch.x = switch.x
    new_switch.y = switch.y
    new_switch.type = "sw"
    new_switch.controller = switch.controller
    new_switch.switch_type = switch.switch_type
    app.switches[switch.name] = switch
    return switch


@app.post("/api/mininet/controllers")
def create_controller(controller: Controller):
    # Create controller in the Mininet network using the request data
    debug(controller)
    controller_type = (controller.controller_type or "").lower()
    if controller.remote or controller_type == "remote":
        # TODO aqui o mininet verifica se a porta está open com timeout de 60s e blocka a request
        new_controller = app.net.addController(
            controller.name,
            controller=RemoteController,
            ip=controller.ip,
            port=controller.port,
        )
    elif controller_type == "ryu":
        if not controller.port:
            raise HTTPException(status_code=400, detail="Ryu controller requires a port")
        if not controller.ryu_app:
            raise HTTPException(status_code=400, detail="Ryu controller requires an app")
        available_apps = list_ryu_apps()
        if controller.ryu_app not in available_apps:
            raise HTTPException(status_code=400, detail="Invalid ryu app")
        controller.ip = controller.ip or "127.0.0.1"
        new_controller = app.net.addController(
            controller.name,
            controller=Ryu,
            ip=controller.ip,
            port=controller.port,
            ryu_app=controller.ryu_app,
        )
    elif controller_type == "nox":
        new_controller = app.net.addController(
            controller.name, controller=NOX
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
def create_link(payload: Union[Tuple[str, str], LinkCreate]):
    if isinstance(payload, (list, tuple)):
        src, dst = payload
        options = None
    else:
        src, dst = payload.src, payload.dst
        options = payload.options

    if src not in app.net.nameToNode or dst not in app.net.nameToNode:
        raise HTTPException(status_code=400, detail=f'node not in net')
    if app.net.nameToNode[src].type == "host" and app.net.nameToNode[src].intfList() and len([i for i in app.net.nameToNode[src].intfList() if i.name and i.name not in ("lo", "lo0")]) >= 1:
        raise HTTPException(status_code=400, detail="host already has a link")
    if app.net.nameToNode[dst].type == "host" and app.net.nameToNode[dst].intfList() and len([i for i in app.net.nameToNode[dst].intfList() if i.name and i.name not in ("lo", "lo0")]) >= 1:
        raise HTTPException(status_code=400, detail="host already has a link")
    key = frozenset((src, dst))
    if key in app.links:
        raise HTTPException(status_code=400, detail=f'link already exists')
    link_kwargs = {}
    if options:
        opt = options.model_dump(exclude_none=True)
        if "delay" in opt and isinstance(opt["delay"], (int, float)):
            opt["delay"] = f"{opt['delay']}ms"
        if "jitter" in opt and isinstance(opt["jitter"], (int, float)):
            opt["jitter"] = f"{opt['jitter']}ms"
        link_kwargs.update(opt)
        link_kwargs["cls"] = TCLink
    new_link = app.net.addLink(src, dst, **link_kwargs)
    if app.net.is_started:
        for node in (src, dst):
            node = app.net.nameToNode[node]
            if node.type in ("host", "nat", "router"):
                node.configDefault()
            elif node.type == "sw" and node.controller:
                # Important, otherwise switch doesnt init the port
                node.start([node.controller])
    # It is important to store this Link object because
    # mininet (apparently) doesn't have an easy way to access this
    app.links[key] = new_link
    if options:
        app.link_attrs[key] = options.model_dump(exclude_none=True)
    else:
        app.link_attrs[key] = {}
    return {"from": src, "to": dst, "options": app.link_attrs[key]}


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
    elif node.type == "nat":
        app.nats[node_id].x = x
        app.nats[node_id].y = y
    elif node.type == "router":
        app.routers[node_id].x = x
        app.routers[node_id].y = y
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
    elif node.type == "nat":
        del app.nats[node_id]
    elif node.type == "router":
        del app.routers[node_id]
    return {"message": f"Node {node_id} deleted successfully"}

@app.delete("/api/mininet/delete_link/{src_id}/{dst_id}")
def delete_link(src_id: str, dst_id: str):
    key = frozenset((src_id, dst_id))
    if key not in app.links:
        raise HTTPException(status_code=404, detail=f"Node not found")
    app.net.delLink(app.links[key])
    del app.links[key]
    app.link_attrs.pop(key, None)
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
    base_data = app.switches.get(node_id) or app.hosts.get(node_id) or app.controllers.get(node_id) or app.nats.get(node_id) or app.routers.get(node_id)
    if not base_data:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    result = dict(**base_data.model_dump())

    if node.type == "sw":
        ports_raw = node.dpctl("dump-ports")
        ports_raw = ports_raw[ports_raw.find("\n") + 1:].replace("\n", " ")
        result["ports"] = [p.strip() for p in ports_raw.split("port") if "LOCAL" not in p and p.strip()]

        flow_table_raw = node.dpctl("dump-flows").strip()
        parsed_flows = []

        for line in flow_table_raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            flow = {}
            match_fields = {}
            actions = None

            if " actions=" in line:
                line, actions = line.split(" actions=", 1)
            elif "actions=" in line:
                line, actions = line.split("actions=", 1)

            if actions is not None:
                flow["actions"] = actions.strip()

            fields = [f.strip() for f in line.split(",") if f.strip()]
            for field in fields:
                if "=" in field:
                    key, value = field.split("=", 1)
                    if key in FLOW_FIELDS:
                        flow[key] = value
                    else:
                        match_fields[key] = value
                else:
                    match_fields[field] = True

            flow["match_fields"] = match_fields
            parsed_flows.append(flow)
        result["flow_table"] = parsed_flows
    elif node.type in ("host", "router"):
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
        default_route = node.cmd("ip route show default").strip()
        result["default_route"] = default_route
        interfaces = []
        try:
            interfaces = [intf.name for intf in node.intfList() if intf.name != "lo"]
        except Exception:
            interfaces = []
        result["interfaces"] = interfaces

    result.pop("x", None)
    result.pop("y", None)
    
    return result

@app.post("/api/mininet/flows")
def add_flow(rule: FlowRuleCreate):
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to add flows")
    if rule.switch not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Switch {rule.switch} not found")
    node = app.net.nameToNode[rule.switch]
    if getattr(node, "type", None) not in ("sw", "switch"):
        raise HTTPException(status_code=400, detail="node is not a switch")

    flow = build_flow(rule)
    cmd = ["ovs-ofctl"]
    if rule.of_version:
        cmd.extend(["-O", rule.of_version])
    cmd.extend(["add-flow", rule.switch, flow])
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ovs-ofctl add-flow failed").strip()
        raise HTTPException(status_code=400, detail=detail)

    return {"status": "ok", "flow": flow}

@app.get("/api/mininet/flows/{switch_id}")
def list_flows(switch_id: str):
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to list flows")
    if switch_id not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Switch {switch_id} not found")
    node = app.net.nameToNode[switch_id]
    if getattr(node, "type", None) not in ("sw", "switch"):
        raise HTTPException(status_code=400, detail="node is not a switch")

    cmd = ["ovs-ofctl", "dump-flows", switch_id]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ovs-ofctl dump-flows failed").strip()
        raise HTTPException(status_code=400, detail=detail)
    return {"switch": switch_id, "flows": result.stdout.strip()}

@app.delete("/api/mininet/flows")
def delete_flows(rule: FlowRuleDelete):
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to delete flows")
    if rule.switch not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Switch {rule.switch} not found")
    node = app.net.nameToNode[rule.switch]
    if getattr(node, "type", None) not in ("sw", "switch"):
        raise HTTPException(status_code=400, detail="node is not a switch")

    match = build_flow_match(rule)
    cmd = ["ovs-ofctl"]
    if rule.of_version:
        cmd.extend(["-O", rule.of_version])
    if rule.strict:
        cmd.append("--strict")
    cmd.extend(["del-flows", rule.switch])
    if match:
        cmd.append(match)
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ovs-ofctl del-flows failed").strip()
        raise HTTPException(status_code=400, detail=detail)

    return {"status": "ok", "match": match or "all"}

def _parse_flow_match_from_dump(line: str) -> str:
    line = line.strip()
    if "actions=" not in line:
        raise ValueError("flow line missing actions")
    head = line.split(" actions=", 1)[0].strip()
    parts = [p.strip() for p in head.split(",") if p.strip()]
    match_parts = []
    cookie_value = None
    table_value = None
    priority_value = None
    skip_keys = {
        "duration",
        "n_packets",
        "n_bytes",
        "idle_timeout",
        "hard_timeout",
    }
    for part in parts:
        if part.startswith("cookie="):
            cookie_value = part.split("=", 1)[1]
            continue
        if part.startswith("table="):
            table_value = part.split("=", 1)[1]
            continue
        if part.startswith("priority="):
            priority_value = part.split("=", 1)[1]
            continue
        key = part.split("=", 1)[0]
        if key in skip_keys:
            continue
        match_parts.append(part)
    if cookie_value:
        if "/" not in cookie_value:
            cookie_value = f"{cookie_value}/-1"
        match_parts.insert(0, f"cookie={cookie_value}")
    if table_value is not None:
        match_parts.insert(0, f"table={table_value}")
    if priority_value is not None:
        match_parts.insert(0, f"priority={priority_value}")
    if not match_parts:
        raise ValueError("could not build match")
    return ",".join(match_parts)

@app.delete("/api/mininet/flows/{switch_id}/{flow_id}")
def delete_flow_by_id(switch_id: str, flow_id: int):
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to delete flows")
    if switch_id not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail=f"Switch {switch_id} not found")
    node = app.net.nameToNode[switch_id]
    if getattr(node, "type", None) not in ("sw", "switch"):
        raise HTTPException(status_code=400, detail="node is not a switch")
    if flow_id <= 0:
        raise HTTPException(status_code=400, detail="flow_id must be >= 1")

    dump = subprocess.run(["ovs-ofctl", "dump-flows", switch_id], text=True, capture_output=True)
    if dump.returncode != 0:
        detail = (dump.stderr or dump.stdout or "ovs-ofctl dump-flows failed").strip()
        raise HTTPException(status_code=400, detail=detail)
    lines = [l for l in dump.stdout.splitlines() if "actions=" in l]
    if flow_id > len(lines):
        raise HTTPException(status_code=404, detail="flow_id not found")
    line = lines[flow_id - 1]
    try:
        match = _parse_flow_match_from_dump(line)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    result = subprocess.run(
        ["ovs-ofctl", "--strict", "del-flows", switch_id, match],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ovs-ofctl del-flows failed").strip()
        raise HTTPException(status_code=400, detail=detail)
    return {"status": "ok", "match": match}

@app.post("/api/mininet/iperf")
def run_iperf(request: IperfRequest):
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started to run iperf")
    if request.client == request.server:
        raise HTTPException(status_code=400, detail="client and server must be different hosts")
    if request.client not in app.net.nameToNode or request.server not in app.net.nameToNode:
        raise HTTPException(status_code=404, detail="client or server host not found")
    client_node = app.net.nameToNode[request.client]
    server_node = app.net.nameToNode[request.server]
    if getattr(client_node, "type", None) != "host" or getattr(server_node, "type", None) != "host":
        raise HTTPException(status_code=400, detail="client and server must be hosts")

    kwargs = {}
    if request.udp_bw:
        kwargs["udpBw"] = request.udp_bw
    if request.fmt:
        kwargs["fmt"] = request.fmt
    if request.seconds:
        kwargs["seconds"] = request.seconds
    if request.port:
        kwargs["port"] = request.port

    result = app.net.iperf(
        hosts=[client_node, server_node],
        l4Type=request.l4_type or "TCP",
        **kwargs,
    )

    if isinstance(result, (list, tuple)) and len(result) >= 2:
        return {"client": result[0], "server": result[1]}
    return {"result": result}

@app.get("/api/mininet/export_script", response_class=PlainTextResponse)
def export_network():
    debug(app.net)
    return export_net_to_script(app.switches, app.hosts, app.controllers, app.nats, app.routers, app.links).encode("utf-8")

@app.get("/api/mininet/export_json", response_class=PlainTextResponse)
def export_network():
    debug(app.net)
    return export_net_to_json(app.switches, app.hosts, app.controllers, app.nats, app.routers, app.links).encode("utf-8")

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

        for router_data in data.get("routers", []):
            router = Router(**router_data)
            create_router(router)

        for nat_data in data.get("nats", []):
            nat = Nat(**nat_data)
            create_nat(nat)

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
            try:
                r, _, _ = select.select([master_fd], [], [], 0)
            except OSError as e:
                if getattr(e, "errno", None) == 9:
                    break
                raise
            if master_fd in r:
                try:
                    output = os.read(master_fd, 1024).decode(errors="ignore")
                except OSError as e:
                    if getattr(e, "errno", None) == 9:
                        break
                    raise
                if output:
                    await websocket.send_text(output)
    except Exception as e:
        debug(f"PTY Read Error: {e}")

async def read_sniffer(process: asyncio.subprocess.Process, websocket: WebSocket):
    """Reads tcpdump output and sends it to WebSocket"""
    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await websocket.send_text(line.decode(errors="ignore").rstrip())
    except Exception as e:
        debug(f"Sniffer Read Error: {e}")


async def start_sniffer_process(node_pid: int, intf: str, pcap_path: str):
    if node_pid and node_pid > 0:
        return await asyncio.create_subprocess_exec(
            "mnexec",
            "-a",
            str(node_pid),
            "tshark",
            "-l",
            "-n",
            "-q",
            "-i",
            intf,
            "-T",
            "ek",
            "-w",
            pcap_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    return await asyncio.create_subprocess_exec(
        "tshark",
        "-l",
        "-n",
        "-q",
        "-i",
        intf,
        "-T",
        "ek",
        "-w",
        pcap_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

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

    env = dict(os.environ)
    env["PS1"] = f"root@{node_id}:\\w$ "
    process = node.popen(
        ["/bin/bash", "--noprofile", "--norc", "-i"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        text=True,
        close_fds=True,
        env=env,
    )

    session_id = f"{node_id}-{uuid.uuid4().hex}"
    sessions = app.terminals.get(node_id, {})
    sessions[session_id] = (master_fd, process)
    app.terminals[node_id] = sessions

    asyncio.create_task(read_pty(master_fd, websocket))

    try:
        while True:
            data = await websocket.receive_text()
            debug("RECEIVED",data.encode())
            os.write(master_fd, data.encode())
    except WebSocketDisconnect:
        process.terminate()
        os.close(master_fd)
        sessions = app.terminals.get(node_id, {})
        sessions.pop(session_id, None)
        if not sessions:
            app.terminals.pop(node_id, None)
        else:
            app.terminals[node_id] = sessions
        print(f"Closed terminal session for {node_id} ({session_id})")

@app.websocket("/api/mininet/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    if not os.path.exists(LOG_FILE):
        clear_log_file()
    process = await asyncio.create_subprocess_exec(
        "tail",
        "-n",
        "1000",
        "-f",
        LOG_FILE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                await asyncio.sleep(0.05)
                continue
            await websocket.send_text(line.decode(errors="ignore").rstrip())
    except WebSocketDisconnect:
        pass
    finally:
        process.terminate()

@app.websocket("/api/mininet/sniffer")
async def websocket_sniffer(websocket: WebSocket):
    """WebSocket endpoint for streaming tcpdump output on all Mininet interfaces"""
    await websocket.accept()

    if not app.net.is_started:
        await websocket.send_text("Error: network must be started to sniff.")
        await websocket.close()
        return

    nodes = list_mininet_interfaces()
    if not nodes:
        await websocket.send_text("Error: no Mininet nodes available to sniff.")
        await websocket.close()
        return

    queue = await app.sniffer_manager.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await app.sniffer_manager.unsubscribe(queue)

@app.get("/api/mininet/sniffer/state")
def sniffer_state():
    return {"active": app.sniffer_manager.active}

@app.get("/api/mininet/sniffer/history")
async def sniffer_history():
    return {"events": await app.sniffer_manager.get_history()}

@app.post("/api/mininet/sniffer/start")
async def sniffer_start():
    await app.sniffer_manager.start()
    return {"active": app.sniffer_manager.active}

@app.post("/api/mininet/sniffer/stop")
async def sniffer_stop():
    await app.sniffer_manager.stop()
    return {"active": app.sniffer_manager.active}

@app.get("/api/mininet/sniffer/export")
async def sniffer_export():
    pcap_data = await app.sniffer_manager.get_pcap()
    return Response(
        content=pcap_data,
        media_type="application/vnd.tcpdump.pcap",
        headers={"Content-Disposition": "attachment; filename=sniffer.pcap"},
    )
