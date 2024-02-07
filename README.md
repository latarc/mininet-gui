# mininet-gui

Frontend and backend API of the Mininet-GUI app

## How to access development VM

Use ssh tunneling:
On your workstation, execute the following commands to start a tunnel in the background. 
Make sure you have the access rights for the VM. In this example, I'm using an alias (mininet-gui-vm) instead of the ip/hostname.
```
# tunnel for frontend
ssh -L 80:127.0.0.1:5173 mininet-gui-vm -N -f

# tunnel for backend
ssh -L 8080:127.0.0.1:8080 mininet-gui-vm -N -f
```

Then access the app on your workstation from <http://localhost>.


## Setup tutorial

This is only a possible configuration for running the app, and it is by far not the best one.
There are countless better ways to do this, but it still works like this.

### Frontend setup

Prerequisites: docker

To run the frontend image, I used this hacky docker command:
```
docker run -w /usr/app -dt -p 0.0.0.0:5173:5173 -u node --name mn-gui-fe -v /home/ubuntu/mininet-gui/mininet-gui-frontend/:/usr/app node /bin/bash -c "npm i && npm run dev"
```

Explaining this spaghetti:
- `-w` sets the workdir to /usr/app
- `-dt` runs the command on a detached (background) terminal
- `-p 0.0.0.0:5173:5173` exposes the default vite port, 5173, so that we can access it through the tunnel
- `-u node` runs the node process with the user `node` instead of `root`
- `--name mn-gui-fe` is self explanatory, just naming the container for convenience
- `-v /home/ubuntu/mininet-gui/mininet-gui-frontend:/usr/app` v stands for volume. this flag mounts the dev directory into the container's /usr/app directory.
- `node` is the tag of the image we'll run
- `/bin/bash -c "npm i && npm run dev"` this one install the dependencies and then `npm run dev` to start the development server.

### Backend setup

Prerequisites: mininet (preferably 2.3.0) installed on python3 (3.10+) and sudo/root permissions

This is a simple step by step to run the backend:

```
cd mininet-gui-backend
sudo pip install -r requirements.txt # ignore the warning which says this is dangerous.
sudo uvicorn mininet_gui_backend.api:app --host=0.0.0.0 --port=8080 --log-level debug
```
