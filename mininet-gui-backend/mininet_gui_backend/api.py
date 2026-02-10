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
import uuid
from datetime import datetime, timezone
from mininet_gui_backend.sniffer import SnifferManager
import pyshark.ek_field_mapping as ek_field_mapping
from pyshark.tshark.output_parser.tshark_ek import TsharkEkJsonParser
from typing import Tuple, Union, Optional, Set
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

from mininet_gui_backend.export import build_addressing_plan, export_net_to_script, export_net_to_json
from mininet_gui_backend.cli import CLISession
from mininet_gui_backend.schema import Switch, Host, Controller, Nat, Router
from mininet_gui_backend.flow_rules import FlowRuleCreate, FlowRuleDelete, build_flow, build_flow_match
from mininet_gui_backend.utils import (
    get_interface_stats_path,
    parse_ip_addrs,
    parse_flow_match_from_dump,
    read_interface_counter,
)

LOG_FILE = os.path.join(os.path.dirname(__file__), "mininet.log")
RYU_APP_DIRS = []

FLOW_FIELDS = [
    "cookie", "duration", "table", "n_packets", "n_bytes", 
    "idle_timeout", "priority", "actions"
]

MONITOR_INTERVAL_SECONDS = 0.5

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


class LinkUpdate(BaseModel):
    src: str
    dst: str
    options: Optional[LinkOptions] = None


class ControllerUpdate(BaseModel):
    controller_type: Optional[str] = None
    remote: Optional[bool] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    ryu_app: Optional[Union[str, list]] = None
    color: Optional[str] = None


class SwitchUpdate(BaseModel):
    of_version: Optional[str] = None


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
    app.iperf_running = False
    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    app.net.is_started = False
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

@app.get("/api/health")
def get_health():
    net = getattr(app, "net", None)
    connected = net is not None
    network_started = bool(getattr(net, "is_started", False))
    status = "ok" if connected else "unavailable"
    return {
        "status": status,
        "connected": connected,
        "network_started": network_started,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

@app.get("/api/ryu/apps")
def get_ryu_apps():
    return {"apps": list_ryu_apps()}


def debug(msg, *args):
    _debug(str(msg)+" "+" ".join(map(str, args))+"\n")

def list_ryu_apps():
    apps = set()
    app_dirs = []
    env_dirs = os.environ.get("RYU_APP_DIRS", "")
    if env_dirs:
        for entry in env_dirs.split(os.pathsep):
            entry = entry.strip()
            if entry:
                app_dirs.append(entry)
    for app_dir in RYU_APP_DIRS:
        if os.path.isdir(app_dir):
            app_dirs.append(app_dir)
    try:
        import importlib
        app_pkg = importlib.import_module("ryu.app")
        if app_pkg and hasattr(app_pkg, "__path__"):
            for _finder, name, _ispkg in pkgutil.iter_modules(app_pkg.__path__):
                if name and not name.startswith("__"):
                    apps.add(name)
            pkg_dir = os.path.dirname(app_pkg.__file__)
            if os.path.isdir(pkg_dir):
                app_dirs.append(pkg_dir)
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["ryu-manager", "--app-list"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.stdout:
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                token = line.split()[0]
                if token.startswith("ryu.app."):
                    apps.add(token[len("ryu.app."):])
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


def add_host_to_net(host: Host):
    host_node = app.net.addHost(host.name, ip=host.ip)
    host_node.x = host.x
    host_node.y = host.y
    host_node.ip = host.ip
    host_node.type = "host"
    return host_node


def add_router_to_net(router: Router):
    params = {"ip": router.ip, "mac": router.mac}
    router_node = app.net.addHost(router.name, cls=LinuxRouter, **params)
    router_node.x = router.x
    router_node.y = router.y
    router_node.ip = router.ip
    router_node.mac = router.mac
    router_node.type = "router"
    return router_node


def add_nat_to_net(nat: Nat):
    params = {}
    if nat.ip:
        params["ip"] = nat.ip
    if nat.mac:
        params["mac"] = nat.mac
    nat_node = app.net.addNAT(nat.name, connect=False, **params)
    nat_node.x = nat.x
    nat_node.y = nat.y
    nat_node.type = "nat"
    if nat.ip:
        nat_node.ip = nat.ip
    if nat.mac:
        nat_node.mac = nat.mac
    return nat_node


def add_controller_to_net(controller: Controller, start=True):
    controller_type = (controller.controller_type or "").lower()
    if controller.remote or controller_type == "remote":
        controller_node = app.net.addController(
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
        ryu_apps = controller.ryu_app if isinstance(controller.ryu_app, list) else [controller.ryu_app]
        available_apps = list_ryu_apps()
        if available_apps and any(app_name not in available_apps for app_name in ryu_apps):
            try:
                import importlib
                for app_name in ryu_apps:
                    importlib.import_module(f"ryu.app.{app_name}")
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid ryu app")
        elif not available_apps:
            try:
                import importlib
                for app_name in ryu_apps:
                    importlib.import_module(f"ryu.app.{app_name}")
            except Exception:
                # If we cannot verify, allow creation to keep UI usable.
                pass
        controller.ip = controller.ip or "127.0.0.1"
        controller_node = app.net.addController(
            controller.name,
            controller=Ryu,
            ip=controller.ip,
            port=controller.port,
            ryu_app=ryu_apps,
        )
    elif controller_type == "nox":
        controller_node = app.net.addController(
            controller.name, controller=NOX
        )
    else:
        if not controller.port or controller.port in _list_listening_ports():
            controller.port = _find_free_controller_port()
        controller_node = app.net.addController(
            controller.name, controller=ReferenceController, port=controller.port
        )

    if start:
        controller_node.start()
    controller_node.x = controller.x
    controller_node.y = controller.y
    controller_node.type = "controller"
    return controller_node


def _list_listening_ports() -> Set[int]:
    result = subprocess.run(
        ["netstat", "-tuln"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "netstat failed").strip()
        raise HTTPException(status_code=500, detail=detail)
    ports: Set[int] = set()
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line or line.lower().startswith("proto"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3]
        if ":" not in local:
            continue
        port_str = local.rsplit(":", 1)[-1]
        if port_str.isdigit():
            ports.add(int(port_str))
    return ports


def _find_free_controller_port() -> int:
    used = _list_listening_ports()
    ranges = [
        range(6633, 6638),
        range(6653, 6658),
    ]
    for rng in ranges:
        for port in rng:
            if port not in used:
                return port
    raise HTTPException(status_code=400, detail="no available controller ports")


def add_switch_to_net(switch: Switch, start=True):
    switch_type = (switch.switch_type or "").lower()
    switch.switch_type = switch_type or switch.switch_type
    if switch_type == "user":
        switch_node = app.net.addSwitch(switch.name, ports=switch.ports, cls=UserSwitch)
    elif switch_type == "ovs":
        switch_node = app.net.addSwitch(switch.name, ports=switch.ports, cls=OVSSwitch)
    elif switch_type == "ovskernel":
        switch_node = app.net.addSwitch(switch.name, ports=switch.ports, cls=OVSKernelSwitch)
    elif switch_type == "ovsbridge":
        switch_node = app.net.addSwitch(switch.name, ports=switch.ports, cls=OVSBridge)
    else:
        switch_node = app.net.addSwitch(switch.name, ports=switch.ports)

    if start and switch.controller:
        switch_node.start([app.net.nameToNode.get(switch.controller)])
    else:
        switch_node.start([])
    switch_node.x = switch.x
    switch_node.y = switch.y
    switch_node.type = "sw"
    switch_node.controller = switch.controller
    switch_node.switch_type = switch.switch_type
    if switch.of_version:
        _apply_switch_openflow_version(switch.name, switch.of_version, switch_type=switch.switch_type)
    return switch_node


def _apply_switch_openflow_version(switch_id: str, of_version: Optional[str], switch_type: Optional[str] = None):
    if switch_type is None:
        switch = app.switches.get(switch_id)
        if not switch:
            raise HTTPException(status_code=404, detail="switch not found")
        switch_type = switch.switch_type
    switch_type = (switch_type or "").lower()
    if switch_type not in ("ovs", "ovskernel", "ovsbridge"):
        raise HTTPException(status_code=400, detail="openflow version is only supported for OVS switches")
    if not of_version or of_version == "auto":
        result = subprocess.run(
            ["ovs-vsctl", "--if-exists", "clear", "bridge", switch_id, "protocols"],
            text=True,
            capture_output=True,
        )
    else:
        result = subprocess.run(
            ["ovs-vsctl", "--if-exists", "set", "bridge", switch_id, f"protocols={of_version}"],
            text=True,
            capture_output=True,
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ovs-vsctl failed").strip()
        raise HTTPException(status_code=400, detail=detail)


def _terminate_all_terminals():
    for node_id, sessions in list(app.terminals.items()):
        for session_id, (master_fd, process) in list(sessions.items()):
            try:
                process.terminate()
            except Exception:
                pass
            try:
                process.wait(timeout=0.1)
            except Exception:
                pass
            try:
                os.close(master_fd)
            except Exception:
                pass
        sessions.clear()
        app.terminals.pop(node_id, None)


async def _stop_all_sniffers_quietly():
    try:
        await app.sniffer_manager.stop()
    except Exception:
        pass


async def _stop_mininet_with_timeout(timeout: float = 5.0):
    controllers = list(getattr(app.net, "controllers", []) or [])
    if controllers:
        for controller in controllers:
            try:
                controller.terminate()
            except Exception:
                pass
    app.net.controllers = []
    loop = asyncio.get_running_loop()
    try:
        await asyncio.wait_for(loop.run_in_executor(None, app.net.stop), timeout=timeout)
    except asyncio.TimeoutError:
        debug(f"mininet.stop() did not complete within {timeout} seconds, continuing cleanup")
    except Exception as exc:
        debug("error while stopping mininet", exc)

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

@app.get("/api/mininet/addressing_plan")
def addressing_plan():
    if not app.net.is_started:
        raise HTTPException(status_code=400, detail="network must be started")
    return build_addressing_plan(app.net)

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
        link = app.links.get(key)
        from_node = nodes[0] if len(nodes) > 0 else None
        to_node = nodes[1] if len(nodes) > 1 else None
        intfs = None
        intf1 = getattr(link, "intf1", None)
        intf2 = getattr(link, "intf2", None)
        if intf1 and intf2 and getattr(intf1, "node", None) and getattr(intf2, "node", None):
            from_node = intf1.node.name
            to_node = intf2.node.name
            intfs = {"from": intf1.name, "to": intf2.name}
        if from_node and to_node:
            edges.append({"from": from_node, "to": to_node, "options": attrs, "intfs": intfs})
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
        controller_id = getattr(app.switches[switch_id], "controller", None)
        controller_node = None
        if controller_id:
            controller_node = app.net.nameToNode.get(controller_id)
        if controller_node:
            switch.controller = controller_node
            switch.start([controller_node])
        else:
            switch.controller = None
            switch.start([])
    app.net.is_started = True
    return {"status": "ok"}

@app.post("/api/mininet/stop")
async def stop_network():
    """Stop network and nodes"""
    await _stop_all_sniffers_quietly()
    _terminate_all_terminals()
    app.iperf_running = False

    await _stop_mininet_with_timeout()

    # Cleanup (mn -c)
    mn_cleanup()

    # Create the Mininet network
    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    app.net.is_started = False
    app.links = dict()
    # Recreate topology without start
    entries = [
        (add_host_to_net, app.hosts.values(), {}),
        (add_router_to_net, app.routers.values(), {}),
        (add_nat_to_net, app.nats.values(), {}),
        (add_controller_to_net, app.controllers.values(), {"start": False}),
        (add_switch_to_net, app.switches.values(), {"start": False}),
    ]
    for builder, collection, kwargs in entries:
        for item in collection:
            builder(item, **kwargs)
    app.links = dict()
    for key, attrs in list(app.link_attrs.items()):
        nodes = list(key)
        if len(nodes) != 2:
            continue
        src, dst = nodes
        kwargs = {}
        if attrs:
            kwargs.update(attrs)
            kwargs["cls"] = TCLink
        new_link = app.net.addLink(src, dst, **kwargs)
        if app.net.is_started:
            for node_id in (src, dst):
                node = app.net.nameToNode[node_id]
                if node.type in ("host", "nat", "router"):
                    node.configDefault()
                elif node.type == "sw" and node.controller:
                    node.start([node.controller])
        app.links[key] = new_link
    return {"status": "ok"}

@app.post("/api/mininet/reset")
async def reset_network():
    """Restart network and nodes"""
    try:
        await app.sniffer_manager.stop()
    except Exception:
        pass
    clear_log_file()
    await stop_network()
    return start_network()

@app.post("/api/mininet/full_reset")
async def full_reset_network():
    """Full reset: stop everything, cleanup, and clear saved topology."""
    await _stop_all_sniffers_quietly()
    _terminate_all_terminals()
    clear_log_file()

    await _stop_mininet_with_timeout()
    mn_cleanup()

    app.controllers = dict()
    app.switches = dict()
    app.hosts = dict()
    app.nats = dict()
    app.routers = dict()
    app.links = dict()
    app.link_attrs = dict()
    app.terminals = dict()
    app.sniffers = dict()
    app.pingall_running = False
    app.iperf_running = False

    setLogLevel("debug")
    app.net = Mininet(autoSetMacs=True, topo=Topo())
    app.net.is_started = False
    return {"status": "ok"}

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
    new_host = add_host_to_net(host)
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
    new_router = add_router_to_net(router)
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
    new_nat = add_nat_to_net(nat)
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
    new_switch = add_switch_to_net(switch)
    app.switches[switch.name] = switch
    return switch


@app.post("/api/mininet/controllers")
def create_controller(controller: Controller):
    # Create controller in the Mininet network using the request data
    debug(controller)
    new_controller = add_controller_to_net(controller, start=True)
    app.controllers[controller.name] = controller
    debug(new_controller)
    return {"status": "ok"}


@app.put("/api/mininet/controllers/{controller_id}")
def update_controller(controller_id: str, payload: ControllerUpdate):
    if controller_id not in app.controllers:
        raise HTTPException(status_code=404, detail="controller not found")
    controller = app.controllers[controller_id]
    updates = payload.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(controller, key, value)
    app.controllers[controller_id] = controller
    return {"controller": controller.model_dump()}


@app.put("/api/mininet/switches/{switch_id}/openflow")
def update_switch_openflow_version(switch_id: str, payload: SwitchUpdate):
    if switch_id not in app.switches:
        raise HTTPException(status_code=404, detail="switch not found")
    of_version = payload.of_version
    if of_version in ("", "auto"):
        of_version = None
    allowed = {None, "OpenFlow10", "OpenFlow11", "OpenFlow12", "OpenFlow13", "OpenFlow14", "OpenFlow15"}
    if of_version not in allowed:
        raise HTTPException(status_code=400, detail="invalid OpenFlow version")
    _apply_switch_openflow_version(switch_id, of_version)
    app.switches[switch_id].of_version = of_version
    return {"switch": app.switches[switch_id].model_dump()}

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
                controller_node = (
                    node.controller
                    if not isinstance(node.controller, str)
                    else app.net.nameToNode.get(node.controller)
                )
                if controller_node:
                    node.controller = controller_node
                    node.start([controller_node])
                else:
                    node.start([])
    # It is important to store this Link object because
    # mininet (apparently) doesn't have an easy way to access this
    app.links[key] = new_link
    if options:
        app.link_attrs[key] = options.model_dump(exclude_none=True)
    else:
        app.link_attrs[key] = {}
    intfs = None
    if getattr(new_link, "intf1", None) and getattr(new_link, "intf2", None):
        intfs = {"from": new_link.intf1.name, "to": new_link.intf2.name}
    return {"from": src, "to": dst, "options": app.link_attrs[key], "intfs": intfs}


@app.put("/api/mininet/links")
def update_link(payload: LinkUpdate):
    src, dst = payload.src, payload.dst
    options = payload.options
    if src not in app.net.nameToNode or dst not in app.net.nameToNode:
        raise HTTPException(status_code=400, detail="node not in net")
    key = frozenset((src, dst))
    if key not in app.links:
        raise HTTPException(status_code=404, detail="link not found")
    stored_opts = options.model_dump(exclude_none=True) if options else {}
    config_opts = dict(stored_opts)
    if "delay" in config_opts and isinstance(config_opts["delay"], (int, float)):
        config_opts["delay"] = f"{config_opts['delay']}ms"
    if "jitter" in config_opts and isinstance(config_opts["jitter"], (int, float)):
        config_opts["jitter"] = f"{config_opts['jitter']}ms"
    app.link_attrs[key] = stored_opts

    link = app.links.get(key)
    if link and config_opts:
        try:
            link.intf1.config(**config_opts)
            link.intf2.config(**config_opts)
        except Exception as exc:
            debug("failed to update link config", exc)

    return {"from": src, "to": dst, "options": app.link_attrs[key]}


@app.get("/api/mininet/links/stats/{src_id}/{dst_id}")
def get_link_stats(src_id: str, dst_id: str):
    key = frozenset((src_id, dst_id))
    link = app.links.get(key)
    if not link:
        raise HTTPException(status_code=404, detail="link not found")
    intfs = []
    for intf in (getattr(link, "intf1", None), getattr(link, "intf2", None)):
        if not intf or not getattr(intf, "name", None):
            continue
        stats_paths = get_interface_stats_path(intf.name)
        intfs.append({
            "name": intf.name,
            "tx_bytes": read_interface_counter(stats_paths["tx"]),
            "rx_bytes": read_interface_counter(stats_paths["rx"]),
        })
    return {
        "from": src_id,
        "to": dst_id,
        "intfs": intfs,
        "options": app.link_attrs.get(key, {}),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


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
        match = parse_flow_match_from_dump(line)
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
    if app.iperf_running:
        raise HTTPException(status_code=409, detail="iperf already running")
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

    app.iperf_running = True
    try:
        result = app.net.iperf(
            hosts=[client_node, server_node],
            l4Type=request.l4_type or "TCP",
            **kwargs,
        )
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            return {"client": result[0], "server": result[1]}
        return {"result": result}
    finally:
        app.iperf_running = False

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

        if "nodes" in data and "edges" in data:
            nodes = data.get("nodes") or []
            edges = data.get("edges") or []
            controllers = []
            switches = []
            hosts = []
            routers = []
            nats = []

            for node in nodes:
                node_type = (node.get("type") or "").lower()
                if node_type in ("controller", "ctl", "c"):
                    controllers.append(node)
                elif node_type in ("sw", "switch"):
                    switches.append(node)
                elif node_type in ("host", "h"):
                    hosts.append(node)
                elif node_type == "router":
                    routers.append(node)
                elif node_type == "nat":
                    nats.append(node)

            controller_ids = {c.get("id") for c in controllers if c.get("id")}
            switch_ids = {s.get("id") for s in switches if s.get("id")}
            switch_index = {s.get("id"): s for s in switches if s.get("id")}

            for edge in edges:
                src = edge.get("from")
                dst = edge.get("to")
                if not src or not dst:
                    continue
                if src in switch_ids and dst in controller_ids:
                    if not switch_index[src].get("controller"):
                        switch_index[src]["controller"] = dst
                elif dst in switch_ids and src in controller_ids:
                    if not switch_index[dst].get("controller"):
                        switch_index[dst]["controller"] = src

            links = []
            for edge in edges:
                src = edge.get("from")
                dst = edge.get("to")
                if not src or not dst:
                    continue
                if src in controller_ids or dst in controller_ids:
                    continue
                options = edge.get("options")
                if options is None:
                    links.append([src, dst])
                else:
                    links.append({"src": src, "dst": dst, "options": options})

            data = {
                "controllers": controllers,
                "switches": switches,
                "hosts": hosts,
                "routers": routers,
                "nats": nats,
                "links": links,
            }

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
            if isinstance(link, dict):
                create_link(LinkCreate(**link))
            else:
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
    if not getattr(app.net, "is_started", False):
        await websocket.send_text("Error: network must be started to open a webshell.")
        await websocket.close()
        return

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


@app.websocket("/api/mininet/monitor")
async def websocket_interface_monitor(websocket: WebSocket):
    """WebSocket endpoint that streams tx/rx traffic rates for a single interface"""
    await websocket.accept()

    if not getattr(app.net, "is_started", False):
        await websocket.send_text("Error: network must be started to monitor.")
        await websocket.close()
        return

    node_id = websocket.query_params.get("node")
    intf_name = websocket.query_params.get("intf")
    interval_param = websocket.query_params.get("interval")
    try:
        interval = float(interval_param) if interval_param else MONITOR_INTERVAL_SECONDS
    except (ValueError, TypeError):
        interval = MONITOR_INTERVAL_SECONDS
    interval = max(0.1, min(interval, 5.0))

    if not node_id or not intf_name:
        await websocket.send_text("Error: node and intf query parameters are required.")
        await websocket.close()
        return

    nodes = list_mininet_interfaces()
    node_info = next((node for node in nodes if node["id"] == node_id), None)
    if not node_info or intf_name not in node_info.get("intfs", []):
        await websocket.send_text(f"Error: interface {intf_name} for node {node_id} was not found.")
        await websocket.close()
        return

    stats = get_interface_stats_path(intf_name)
    tx_path = stats.get("tx")
    rx_path = stats.get("rx")
    if not tx_path or not rx_path or not os.path.isdir(os.path.dirname(tx_path)):
        await websocket.send_text(f"Error: statistics for interface {intf_name} are unavailable.")
        await websocket.close()
        return

    last_tx = None
    last_rx = None
    last_time = None
    try:
        while True:
            current_time = datetime.now(timezone.utc)
            tx_bytes = read_interface_counter(tx_path)
            rx_bytes = read_interface_counter(rx_path)
            if tx_bytes is None or rx_bytes is None:
                await websocket.send_text(f"Error: failed to read counters for {intf_name}.")
                break

            if last_tx is not None and last_rx is not None and last_time:
                elapsed = (current_time - last_time).total_seconds()
                if elapsed > 0:
                    tx_delta = max(0, tx_bytes - last_tx)
                    rx_delta = max(0, rx_bytes - last_rx)
                    tx_gbps = (tx_delta * 8) / elapsed / 1e9
                    rx_gbps = (rx_delta * 8) / elapsed / 1e9
                    payload = {
                        "node": node_id,
                        "intf": intf_name,
                        "ts": current_time.isoformat(),
                        "tx_gbps": tx_gbps,
                        "rx_gbps": rx_gbps,
                    }
                    await websocket.send_json(payload)

            last_tx = tx_bytes
            last_rx = rx_bytes
            last_time = current_time
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        debug(f"Monitor WebSocket error: {exc}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

@app.get("/api/mininet/sniffer/state")
def sniffer_state():
    return {"active": app.sniffer_manager.active}

@app.get("/api/mininet/sniffer/history")
async def sniffer_history():
    return {"events": await app.sniffer_manager.get_history()}

@app.post("/api/mininet/sniffer/start")
async def sniffer_start():
    if not getattr(app.net, "is_started", False):
        raise HTTPException(status_code=400, detail="network must be started to begin sniffing")
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
