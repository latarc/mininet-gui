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


def export_net_to_script(net) -> str:
    script = SCRIPT_TEMPLATE
    return script