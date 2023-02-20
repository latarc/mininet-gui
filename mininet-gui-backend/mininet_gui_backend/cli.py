from mininet.cli import CLI

# use https://github.com/mininet/mininet/blob/master/mininet/term.py#L1 ?
# and https://github.com/python/cpython/blob/3.11/Lib/cmd.py
# and https://fastapi.tiangolo.com/advanced/websockets/
# and https://docs.python.org/3/library/cmd.html
# and https://github.com/mininet/mininet/blob/master/examples/sshd.py#L21

# check if host is connected, test conn

class CLISession:
    def __init__(self):
        self.url = ""
        self.detach_and_listen()

    def detach_and_listen(self):
        #listen on self.url
        #detach from main
        raise NotImplemented
        