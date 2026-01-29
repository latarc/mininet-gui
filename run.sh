#!/bin/bash

sudo pkill uvicorn
sudo pkill vite


MININET_GUI_DIR="$HOME/mininet-gui"
BACKEND_DIR="$MININET_GUI_DIR/mininet-gui-backend"
FRONTEND_DIR="$MININET_GUI_DIR/mininet-gui-frontend"

export MININET_GUI_ADDRESS="192.168.56.103"

echo "Running mininet-gui-backend in background"
(cd $BACKEND_DIR ; sudo nohup uvicorn mininet_gui_backend.api:app --host=0.0.0.0 --port=8000 --log-level debug &)

echo "VITE_BACKEND_URL=http://$MININET_GUI_ADDRESS:8000" > $FRONTEND_DIR/.env
echo "VITE_BACKEND_WS_URL=ws://$MININET_GUI_ADDRESS:8000" >> $FRONTEND_DIR/.env

echo "Running mininet-gui-frontend in background"
(cd $FRONTEND_DIR ; nvm use 18.20.7 ; nohup npm run dev -- --host 0.0.0.0 &)

echo "Mininet-GUI bootstrap complete"
echo "Backend log file: $BACKEND_DIR/nohup.out"
echo "Frontend log file: $FRONTEND_DIR/nohup.out"


echo -e "\n\n#### Mininet-GUI is available at: ####\n"
echo "http://$MININET_GUI_ADDRESS:5173"
