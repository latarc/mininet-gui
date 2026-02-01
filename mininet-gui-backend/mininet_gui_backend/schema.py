from typing import Union

from pydantic import BaseModel
from mininet.node import RemoteController, NOX, UserSwitch, OVSSwitch, OVSKernelSwitch, OVSBridge
from mininet_gui_backend.nodes import Ryu


class Node(BaseModel):
    id: str
    type: str
    name: str
    label: str
    x: float
    y: float


class Controller(Node):
    controller_type: str = "default"
    remote: bool
    ip: Union[str, None]
    port: Union[int, None]
    ryu_app: Union[str, None] = None
    color: Union[str, None] = None

    def format_controller(self) -> str:
        controller_type = (self.controller_type or "").lower()
        if self.remote or controller_type == "remote":
            return f'{self.name} = net.addController("{self.name}", controller=RemoteController, ip="{self.ip}", port={self.port})'
        if controller_type == "ryu":
            return f'{self.name} = net.addController("{self.name}", controller=Ryu, ip="{self.ip or "127.0.0.1"}", port={self.port}, ryu_app="{self.ryu_app}")'
        if controller_type == "nox":
            return f'{self.name} = net.addController("{self.name}", controller=NOX)'
        return f'{self.name} = net.addController("{self.name}")'


class Host(Node):
    ip: str
    mac: str


class Router(Node):
    ip: str
    mac: str

    def format_router(self) -> str:
        return f'{self.name} = net.addHost("{self.name}", cls=LinuxRouter, ip="{self.ip}", mac="{self.mac}")'


class Nat(Node):
    ip: Union[str, None]
    mac: Union[str, None]

    def format_nat(self) -> str:
        params = []
        if self.ip:
            params.append(f'ip="{self.ip}"')
        if self.mac:
            params.append(f'mac="{self.mac}"')
        params_str = ", ".join(params)
        if params_str:
            params_str = f", {params_str}"
        return f'{self.name} = net.addNAT("{self.name}", connect=None{params_str})'


class Switch(Node):
    ports: int
    controller: Union[str, None]
    switch_type: str = "ovskernel"

    def format_switch(self) -> str:
        switch_type = (self.switch_type or "").lower()
        if switch_type == "user":
            return f'{self.name} = net.addSwitch("{self.name}", cls=UserSwitch)'
        if switch_type == "ovs":
            return f'{self.name} = net.addSwitch("{self.name}", cls=OVSSwitch)'
        if switch_type == "ovskernel":
            return f'{self.name} = net.addSwitch("{self.name}", cls=OVSKernelSwitch)'
        if switch_type == "ovsbridge":
            return f'{self.name} = net.addSwitch("{self.name}", cls=OVSBridge)'
        return f'{self.name} = net.addSwitch("{self.name}")'
