#!/bin/bash
# CloudBrowser — Start Script
# Hyperbrowser equivalent for JackConnect

set -e

RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[1;33m'; BLU='\033[0;34m'
PORT=${CLOUDBROWSER_PORT:-9876}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 CloudBrowser — Browser Infra for AI Agents"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check dependencies
check() {
  if command -v python3 &>/dev/null; then
    echo -e "  ${GRN}✅${RST} Python3: $(python3 --version | awk '{print $2}')"
  else
    echo -e "  ${RED}❌${RST} Python3 not found"
    exit 1
  fi
}

echo "Checking dependencies..."
check

# Install Python deps if needed
install_deps() {
  echo "Installing dependencies..."
  pip install --quiet flask flask-cors browser-use langchain langchain-ollama Pillow requests 2>&1 | tail -2
  echo -e "  ${GRN}✅${RST} Dependencies installed"
}

pip show flask &>/dev/null || install_deps

# Start the server
echo ""
echo "Starting CloudBrowser API on port $PORT..."

# Kill existing instance
pkill -f "cloudbrowser.*server.py" 2>/dev/null || true
sleep 1

# Start in background
nohup python3 /home/workspace/jack-connect/cloud-browser/server.py \
  >> /tmp/cloudbrowser.log 2>&1 &

CBPID=$!
echo $CBPID > /tmp/cloudbrowser.pid

sleep 2

# Verify
if curl -sf --max-time 3 http://localhost:$PORT/health >/dev/null 2>&1; then
  echo ""
  echo -e "  ${GRN}✅${RST} CloudBrowser API: http://localhost:$PORT"
  echo ""
  echo "Endpoints:"
  echo "  POST   /session           — create isolated browser"
  echo "  DELETE /session/{id}     — kill session"
  echo "  GET    /sessions          — list active sessions"
  echo "  POST   /task              — run browser task"
  echo "  GET    /task/{id}         — get task result"
  echo "  GET    /screenshot/{id}   — get screenshot"
  echo "  GET    /recording/{id}    — get recording"
  echo ""
  echo "PID: $CBPID | Log: /tmp/cloudbrowser.log"
  echo ""
  echo "Quick test:"
  echo "  curl -X POST http://localhost:$PORT/session"
else
  echo -e "  ${RED}❌${RST} Failed to start — check /tmp/cloudbrowser.log"
  tail -20 /tmp/cloudbrowser.log
fi
