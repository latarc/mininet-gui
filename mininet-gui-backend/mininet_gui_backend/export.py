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
    return


def add_links(script, links):
    return

def start_nodes(script, nodes):
    return

def export_net_to_script(net) -> str:
    script = SCRIPT_TEMPLATE
    add_nodes(script)
    add_links(script)
    start_nodes(script)
    return script

def import_script(script):
    for line in script.splitlines():
        eval(line)
