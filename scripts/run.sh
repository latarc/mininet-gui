#!/bin/bash
set -euo pipefail

echo "Stopping previous processes..."
sudo pkill -9 -f "uvicorn|mininet_gui_backend.api" || true
sudo pkill -9 -f "npm run dev|vite" || true
sudo pkill -9 -f "tshark|dumpcap" || true
sudo pkill -9 -f "ryu" || true
sudo pkill -9 -f "mnexec" || true
sudo pkill -9 -f "mininet:" || true
sudo mn -c >/dev/null 2>&1 || true


MININET_GUI_DIR="$HOME/mininet-gui"
BACKEND_DIR="$MININET_GUI_DIR/mininet-gui-backend"
FRONTEND_DIR="$MININET_GUI_DIR/mininet-gui-frontend"

export MININET_GUI_ADDRESS="192.168.56.103"

trim_log() {
  local file="$1"
  if [ -f "$file" ]; then
    tail -n 10000 "$file" > "${file}.tmp"
    mv "${file}.tmp" "$file"
  fi
}

trim_log "$BACKEND_DIR/nohup.out"
trim_log "$FRONTEND_DIR/nohup.out"

echo "Running mininet-gui-backend in background"
(cd $BACKEND_DIR ; sudo nohup uvicorn mininet_gui_backend.api:app --host=0.0.0.0 --port=8000 --log-level debug &)

echo "VITE_BACKEND_URL=http://$MININET_GUI_ADDRESS:8000" > $FRONTEND_DIR/.env
echo "VITE_BACKEND_WS_URL=ws://$MININET_GUI_ADDRESS:8000" >> $FRONTEND_DIR/.env

echo "Running mininet-gui-frontend in background"
(
  cd $FRONTEND_DIR
  if command -v nvm >/dev/null 2>&1; then
    nvm use 18.20.7
  elif [ -s "$HOME/.nvm/nvm.sh" ]; then
    . "$HOME/.nvm/nvm.sh"
    nvm use 18.20.7 || true
  elif [ -s "/usr/share/nvm/nvm.sh" ]; then
    . "/usr/share/nvm/nvm.sh"
    nvm use 18.20.7 || true
  fi
  nohup npm run dev -- --host 0.0.0.0 &
)

echo "Mininet-GUI bootstrap complete"
echo "Backend log file: $BACKEND_DIR/nohup.out"
echo "Frontend log file: $FRONTEND_DIR/nohup.out"


echo -e "\n\n#### Mininet-GUI is available at: ####\n"
echo "http://$MININET_GUI_ADDRESS:5173"
