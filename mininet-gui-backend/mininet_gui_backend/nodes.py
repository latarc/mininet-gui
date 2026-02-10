from mininet.node import Node
from mininet.util import errRun
from mininet.moduledeps import pathCheck


class Ryu(Node):
    """Ryu controller node."""

    def __init__(
        self,
        name,
        inNamespace=False,
        ip="127.0.0.1",
        port=6653,
        ryu_app="simple_switch_13",
        **params,
    ):
        self.ip = ip
        self.port = int(port)
        if isinstance(ryu_app, list):
            self.ryu_app = [str(app) for app in ryu_app]
        else:
            self.ryu_app = [str(ryu_app)]
        # TODO: Make OpenFlow version configurable; force OF13 for now.
        self.ofp_version = "OpenFlow13"
        self.protocol = "tcp"
        self.ryu_pid = None
        Node.__init__(self, name, inNamespace=inNamespace, ip=ip, **params)
        self.checkListening()

    def checkListening(self):
        out, _err, returnCode = errRun("which telnet")
        if "telnet" not in out or returnCode != 0:
            raise Exception(
                "Error running telnet to check for listening controllers; please check that it is installed."
            )
        listening = self.cmd("echo A | telnet -e A %s %d" % (self.ip, self.port))
        if "Connected" in listening:
            servers = self.cmd("netstat -natp").split("\n")
            pstr = ":%d " % self.port
            clist = servers[0:1] + [s for s in servers if pstr in s]
            raise Exception(
                "Please shut down the controller which is running on port %d:\n"
                % self.port
                + "\n".join(clist)
            )

    def start(self):
        pathCheck("ryu")
        cout = "/tmp/" + self.name + ".log"
        apps = " ".join(f"ryu.app.{app}" for app in self.ryu_app if app)
        cmd = (
            "ryu run --observe-links --ofp-tcp-listen-port %d %s"
            % (self.port, apps)
        )
        pid = self.cmd(cmd + " 1>" + cout + " 2>" + cout + " & echo $!")
        try:
            self.ryu_pid = int(pid.strip())
        except Exception:
            self.ryu_pid = None
        self.execed = False

    def IP(self, intf=None):
        return self.ip

    def stop(self, *args, **kwargs):
        if self.ryu_pid:
            try:
                import os
                import signal
                os.kill(self.ryu_pid, signal.SIGTERM)
            except Exception:
                pass
        elif self.shell:
            self.cmd("kill %ryu")
        if self.shell:
            super(Ryu, self).stop(*args, **kwargs)
