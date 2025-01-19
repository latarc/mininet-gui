from typing import Union

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    type: str
    name: str
    label: str
    x: float
    y: float


class Controller(Node):
    remote: bool
    ip: Union[str, None]
    port: Union[int, None]


class Host(Node):
    ip: str
    mac: str


class Switch(Node):
    ports: int
    controller: Union[str, None]