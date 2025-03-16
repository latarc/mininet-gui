#!/bin/bash

sudo pkill uvicorn
sudo pkill vite

FRONTEND_DIR=$PWD/mininet-gui-frontend
BACKEND_DIR=$PWD/mininet-gui-backend

echo "Running mininet-gui-backend in background"
(cd $BACKEND_DIR ; sudo nohup uvicorn mininet_gui_backend.api:app --host=0.0.0.0 --port=8000 --log-level debug &)

echo "Running mininet-gui-frontend in background"
(cd $FRONTEND_DIR ; nohup npm run dev &)

echo "Mininet-GUI bootstrap complete"
echo "Backend log file: $BACKEND_DIR/nohup.out"
echo "Frontend log file: $FRONTEND_DIR/nohup.out"

export MININET_GUI_ADDRESS=$(hostname --all-ip-addresses | awk '{print $1}'  )

echo -e "\n\n#### Mininet-GUI is available at: ####\n"
echo "http://$MININET_GUI_ADDRESS:5173"