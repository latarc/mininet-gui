# Mininet-GUI: A Visual and Interactive Approach to SDN Experimentation

![mininet-gui logo](https://github.com/user-attachments/assets/c3c35610-1d7b-4458-a08e-2f9608816501)

Mininet-GUI is a web-based interface to design and run Mininet experiments through an interactive topology graph. The user can add and configure hosts, switches, controllers, and links, start/stop the emulation, and modify the topology during execution.
Mininet-GUI also provides integrated access to node terminals via WebShell, an OpenFlow flow-rule manager, a packet analyzer with a built-in Sniffer, real-time traffic charts, and a Chat interface to interact with the topology using AI.
The platform was designed to reduce the complexity of SDN experimentation, making Mininet more accessible for beginners and more efficient for researchers

## Project information

Contact: Lucas Schneider <lucasschneider.dev@gmail.com>

Paper link: <https://1drv.ms/b/c/75254e252c7d0ebe/EWzabHAvMyFEoawJRxAa0fcBwRgmczsjGMxyTq2DMsi5-w?e=Wc0xK3>

Demo video: <https://youtu.be/YSsqHKsJlxY>

Official repository: <https://github.com/latarc/mininet-gui>

### Screenshot

![mininet-gui screenshot](https://github.com/user-attachments/assets/1d5bfc10-859e-4385-96ac-f8f366e14b5a)

## Requirements

The ready-to-use VM requires Oracle VirtualBox (version 7.1.6 r167084).
RAM: minimum 8 GB for the VM.

## Security note

Native Mininet installation is invasive and may modify or remove important system files. For safety, the ready-to-use Mininet-GUI VM is recommended.

## Installation

### 1) Docker (recommended for local use)

Prerequisites:
- Docker
- Open vSwitch installed and configured on the host

Build:

```bash
docker build -t mininet-gui \
  --build-arg VITE_BACKEND_URL=http://localhost:8000 \
  --build-arg VITE_BACKEND_WS_URL=ws://localhost:8000 \
  .
```

Run:

```bash
docker run --privileged --net=host \
  -v /var/run/openvswitch:/var/run/openvswitch \
  mininet-gui
```

Open the UI:
`http://localhost:5173`

### 2) From source

Warning: the commands below modify the kernel and other system settings. Use with caution.
Tested on Ubuntu 20.04.

```bash
git clone https://github.com/mininet/mininet
cd mininet
./util/install.sh -nfv
cd ..
git clone https://github.com/latarc/mininet-gui
cd mininet-gui
./setup.sh
```

Optional Ryu installation:

```bash
pip3 install ryu eventlet==0.30.0 dnspython==1.16.0
```

### 3) Ready-to-use VM (recommended)

Prerequisites: Oracle VirtualBox (<https://www.virtualbox.org/wiki/Downloads>)

Step 1: Download the OVA file here: <https://drive.google.com/file/d/1HBqlTwEWnmkPjRFJVQhEn34itKNyzhg3/view?usp=sharing>

Step 2: Import `Mininet-GUI-Desktop-VM-SBRC-2025.ova` into VirtualBox

Step 3: Start the VM (user `mininet`, password `mininet`)

## Minimal test

Step 1: Start the VM and log in (user `mininet`, password `mininet`)

Step 2: Open a terminal (Ctrl+Alt+T) and run: `mininet_gui` (or `/home/mininet/mininet-gui/run.sh`)

Step 3: The command prints a URL (example: `http://10.0.2.15:5173`). Open it in a browser inside the VM.

Step 4: Create a controller by dragging the "Controller" icon from the left sidebar to the canvas. When prompted, choose "Default" and submit.

Step 5: Click "Generate Topology" in the left sidebar. In the modal, select "Topology Type" Single, "Controller" c1, set "Hosts" to 2, then submit.

Step 6: Run a pingall test by clicking "Run Pingall Test" on the left sidebar and wait for results.

Step 7 (optional): iperf test. In the WebShell, open h1 and run `iperf -s`. Open h2 and run `iperf -c 10.0.0.1`. Wait about 1 minute.

Step 8 (optional): Multiple controllers. Add a new "Controller" with type "Remote" and set IP 127.0.0.1, port 6633. Generate a Single topology with 2 hosts and select the new controller (c2). Connect the two switches (s1 and s2) using "Create Link". In the WebShell for c2, run `ryu-manager --ofp-tcp-listen-port 6633 ryu.app.simple_switch_13` to start the Ryu SDN controller. Test with Pingall.

Step 9: Click "Export Topology (JSON)" and "Export Mininet Script" to export the current topology as JSON and as a Python Mininet script.

## Experiments

The VM requires at least 2 GB of RAM and one CPU core.

### Claim: Automated topology generation with common models

After starting mininet_gui and opening the frontend, click "Generate Topology". Select the topology type (Single, Linear, or Tree) and number of devices, then click OK.

### Claim: Integrated terminal for nodes via WebShell

After starting mininet_gui and opening the frontend, create at least one node (via the topology generator or drag-and-drop). In the bottom tab labeled "Webshell", select the tab for that node and run bash commands inside that node’s namespace.

## LICENSE

BSD 3-Clause License

Copyright (c) 2025, LaTARC Research Lab

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
