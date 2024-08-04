# mininet-gui

Frontend and backend API of the Mininet-GUI app

## Setup tutorial

This is one possible setup for running the app, although it may not be the best.

### Frontend setup

Prerequisites: docker

To run the frontend image, I used this docker command:
```
docker run -w /usr/app -dt -p 0.0.0.0:5173:5173 -u node --name mn-gui-fe -v /home/ubuntu/mininet-gui/mininet-gui-frontend/:/usr/app node /bin/bash -c "npm i && npm run dev"
```

Explanation:
- `-w` sets the workdir to /usr/app
- `-dt` runs the command on a detached (background) terminal
- `-p 0.0.0.0:5173:5173` exposes the default vite port, 5173
- `-u node` runs the process with user `node` instead of `root`
- `--name mn-gui-fe` name of the container
- `-v /home/ubuntu/mininet-gui/mininet-gui-frontend:/usr/app` v stands for volume. this flag mounts the dev directory into the container's /usr/app directory.
- `node` is the tag of the image we'll run
- `/bin/bash -c "npm i && npm run dev"` this one installs the dependencies and then runs `npm run dev` to start the development server.

### Backend setup

Prerequisites: mininet (preferably 2.3.0) installed on python3 (3.10+) and sudo/root permissions

This is a simple step by step to run the backend:

```
cd mininet-gui-backend
sudo pip install -r requirements.txt # ignore the warning which says this is dangerous.
sudo uvicorn mininet_gui_backend.api:app --host=0.0.0.0 --port=8080 --log-level debug
```
