#!/bin/bash

sudo apt update && sudo apt install -y curl npm

export BACKEND_DIR=$PWD/mininet-gui-backend
export FRONTEND_DIR=$PWD/mininet-gui-frontend

echo "Installing backend deps"
(cd $BACKEND_DIR ; sudo python3 -m pip install -r requirements.txt)

echo "Installing nvm"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash

echo "Installing node 18.20.7"
export NVM_DIR="$HOME/.nvm"
source $NVM_DIR/nvm.sh

nvm install 18.20.7

echo "Installing frontend deps"
(cd $FRONTEND_DIR ; npm install)

