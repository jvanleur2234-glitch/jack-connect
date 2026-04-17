#!/bin/bash
# JackConnect Dashboard — Launcher
# Starts Homepage (real estate dashboard) + all JackConnect services

set -e

RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[1;33m'; BLU='\033[0;34m'; RST='\033[0m'
INFO(){ printf "${BLU}[INFO]${RST} %s\n" "$*"; }
OK(){ printf "${GRN}[OK]${RST} %s\n" "$*"; }
WARN(){ printf "${YEL}[WARN]${RST} %s\n" "$*"; }

cat << 'BANNER'
   ╔═══════════════════════════════════════╗
   ║   JackConnect Dashboard               ║
   ║   Real Estate Command Center          ║
   ╚═══════════════════════════════════════╝
BANNER
echo

# ── Check Docker ──────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    WARN "Docker not found. Starting Homepage from source instead."
    SOURCE_MODE=true
fi

# ── Option 1: Docker (recommended) ──────────────────────────────────────────
start_docker() {
    INFO "Starting JackConnect Dashboard via Docker..."
    
    DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)/jack-dashboard"
    
    # Start Homepage dashboard
    docker run -d \
        --name jack-dashboard \
        -p 3001:3000 \
        -v "$DASHBOARD_DIR/config:/app/config:ro" \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -e HOMEPAGE_ALLOWED_HOSTS="localhost,127.0.0.1" \
        -e PUID=1000 \
        -e PGID=1000 \
        --restart unless-stopped \
        ghcr.io/gethomepage/homepage:latest
    
    OK "Dashboard: http://localhost:3001"
}

# ── Option 2: From source ─────────────────────────────────────────────────
start_source() {
    INFO "Starting JackConnect Dashboard from source..."
    
    DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)"
    
    if [[ ! -d "homepage/node_modules" ]]; then
        INFO "Installing Homepage dependencies..."
        cd homepage && npm install 2>&1 | tail -3 && cd ..
    fi
    
    # Copy config
    cp -r "$DASHBOARD_DIR/jack-dashboard/config/" "$DASHBOARD_DIR/homepage/config/"
    
    cd homepage
    PORT=3001 nohup pnpm start >> "$DASHBOARD_DIR/logs/dashboard.log" 2>&1 &
    cd ..
    
    OK "Dashboard: http://localhost:3001"
}

# ── Start Cognee Memory ────────────────────────────────────────────────────
start_cognee() {
    INFO "Starting Cognee memory layer..."
    
    MEMORY_DIR="$HOME/.jack-connect/memory"
    mkdir -p "$MEMORY_DIR"
    
    # Check if cognee is installed
    if python3 -c "import cognee" 2>/dev/null; then
        cd "$(dirname "$0")"
        nohup python3 cognee-jack.py status > "$HOME/.jack-connect/logs/cognee.log" 2>&1 &
        OK "Cognee memory: http://localhost:8000"
    else
        WARN "Cognee not installed. Run: uv pip install cognee"
    fi
}

# ── Main ───────────────────────────────────────────────────────────────────
main() {
    mkdir -p ~/jack-connect/logs ~/.jack-connect/memory ~/.jack-connect/logs
    
    if [[ ${SOURCE_MODE:-false} != true ]]; then
        start_docker
    else
        start_source
    fi
    
    start_cognee
    
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    OK "JackConnect Dashboard is LIVE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🏠 Dashboard:   http://localhost:3001"
    echo "  🧠 Memory API:  http://localhost:8000"
    echo
    echo "  Ctrl+C to stop"
}

main "$@"
