import json
from typing import List, Tuple, Union

from mininet_gui_backend.schema import Host, Switch, Controller


SCRIPT_TEMPLATE = """
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, Host
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

setLogLevel("info")

net = Mininet(controller=Controller, switch=OVSKernelSwitch, host=Host, link=TCLink)

# Controllers
{controllers}

# Switches
{switches}

# Hosts
{hosts}

# Links
{links}

net.build()

{controller_start}

{switch_start}

print("\\nNetwork topology created successfully!\\n")

CLI(net)  # Start Mininet CLI

net.stop()
"""


def export_net_to_script(
    switches: List[Switch], 
    hosts: List[Host], 
    controllers: List[Controller], 
    links: List[Tuple[str, str]]
) -> str:
    template = str(SCRIPT_TEMPLATE)

    controllers_str = "\n".join([
        f'{c.name} = net.addController("{c.name}", controller=RemoteController, ip="{c.ip}", port={c.port})'
        if c.remote else f'{c.name} = net.addController("{c.name}")'
        for c in controllers.values()
    ])

    switches_str = "\n".join([
        f'{s.name} = net.addSwitch("{s.name}")' for s in switches.values()
    ])

    hosts_str = "\n".join([
        f'{h.name} = net.addHost("{h.name}", ip="{h.ip}", mac="{h.mac}")' for h in hosts.values()
    ])

    links_str = "\n".join([
        f'net.addLink({link_list[0]}, {link_list[1]})'
        for link_list in (list(link) for link in links.keys())
    ])

    controller_start_str = "\n".join([
        f"{c.name}.start()" for c in controllers.values()
    ])

    switch_start_str = "\n".join([
        f'{s.name}.start([{s.controller}])' if s.controller else f'{s.name}.start([])'
        for s in switches.values()
    ])

    return template.format(
        controllers=controllers_str,
        switches=switches_str,
        hosts=hosts_str,
        links=links_str,
        controller_start=controller_start_str,
        switch_start=switch_start_str
    )

# def import_script(script):
#     for line in script.splitlines():
#         eval(line)


# json schema
def export_net_to_json(
    switches: List[Switch], 
    hosts: List[Host], 
    controllers: List[Controller], 
    links: List[Tuple[str, str]]
) -> str:
    net_data = {
        "switches": [switch.dict() for switch in switches.values()],
        "hosts": [host.dict() for host in hosts.values()],
        "controllers": [controller.dict() for controller in controllers.values()],
        "links": [list(link) for link in links]
    }

    return json.dumps(net_data, indent=4)
