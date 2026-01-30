#!/bin/bash
set -euo pipefail

echo "Stopping Mininet-GUI processes..."
sudo pkill -9 -f "uvicorn|mininet_gui_backend.api" || true
sudo pkill -9 -f "npm run dev|vite" || true
sudo pkill -9 -f "tshark|dumpcap" || true
sudo pkill -9 -f "mnexec" || true
sudo pkill -9 -f "mininet:" || true
sudo mn -c >/dev/null 2>&1 || true

echo "Stopped."
