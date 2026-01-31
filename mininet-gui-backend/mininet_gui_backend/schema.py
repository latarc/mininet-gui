from typing import Union

from pydantic import BaseModel
from mininet.node import RemoteController, Ryu, NOX


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

    def format_controller(self) -> str:
        controller_type = (self.controller_type or "").lower()
        if self.remote or controller_type == "remote":
            return f'{self.name} = net.addController("{self.name}", controller=RemoteController, ip="{self.ip}", port={self.port})'
        if controller_type == "ryu":
            return f'{self.name} = net.addController("{self.name}", controller=Ryu)'
        if controller_type == "nox":
            return f'{self.name} = net.addController("{self.name}", controller=NOX)'
        return f'{self.name} = net.addController("{self.name}")'


class Host(Node):
    ip: str
    mac: str


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
