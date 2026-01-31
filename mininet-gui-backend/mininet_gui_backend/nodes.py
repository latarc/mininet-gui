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
        self.ryu_app = ryu_app
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
        cmd = (
            "ryu run --ofp-tcp-listen-port %d ryu.app.%s"
            % (self.port, self.ryu_app)
        )
        pid = self.cmd(cmd + " 1>" + cout + " 2>" + cout + " & echo $!")
        try:
            self.ryu_pid = int(pid.strip())
        except Exception:
            self.ryu_pid = None
        self.execed = False

    def stop(self, *args, **kwargs):
        if self.ryu_pid:
            self.cmd("kill %s" % self.ryu_pid)
        else:
            self.cmd("kill %ryu")
        super(Ryu, self).stop(*args, **kwargs)
