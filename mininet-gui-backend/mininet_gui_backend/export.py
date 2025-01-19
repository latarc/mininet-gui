import json
from typing import List, Dict, Union

from mininet_gui_backend.schema import Host, Switch, Controller


SCRIPT_TEMPLATE = """#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.cli import CLI

net = Mininet({mininet_params})

{add_nodes}
{add_links}

{start_nodes}

net.start()
CLI(net)
net.stop()

"""


def add_nodes(script, nodes):
    node_add_code = []
    for node in nodes:
        params = nodes[node].params
        parsed_params = ",".join([f'{param}="{params[param]}"' for param in params])
        if node.startswith("s"):
            node_add_code.append(f"net.addSwitch({parsed_params})\n")
        if node.startswith("h"):
            node_add_code.append(f"net.addHost({parsed_params})\n")
    print(node_add_code, script)
    return script.replace("{add_nodes}", "".join(node_add_code))


def add_links(script, links):
    link_add_code = []
    for link in links:
        link_add_code.append(f"net.addLink({link[0]}, {link[1]})\n")
    return script.replace("{add_links}", "".join(link_add_code))


def start_nodes(script, nodes):
    start_nodes_code = []

    return script.replace("{add_links}", "".join(start_nodes_code))


def export_net_to_script(net) -> str:
    script = add_nodes(SCRIPT_TEMPLATE, net.nameToNode)
    # add_links(script, net.links)
    # start_nodes(script, net.nodes)
    return script


# def import_script(script):
#     for line in script.splitlines():
#         eval(line)


# json schema
def export_net_to_json(
    switches: List[Switch], 
    hosts: List[Host], 
    controllers: List[Controller], 
    links: List[Dict[str, str]]
) -> str:
    net_data = {
        "switches": [switch.dict() for switch in switches.values()],
        "hosts": [host.dict() for host in hosts.values()],
        "controllers": [controller.dict() for controller in controllers.values()],
        "links": [link["tuple"] for link in links.values()]
    }
    
    return json.dumps(net_data, indent=4)
