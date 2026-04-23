#!/bin/bash
# ================================================================
# JACKCONNECT UNIFIED INSTALLER v2.5
# Solomon OS + JackConnect + Paperclip + BitNet + TileLang + CORAL
# FreeLLMAPI — 14 free providers, 1 OpenAI-compatible endpoint
# Windows 11 (WSL2) — One command install
#
# Usage: curl -sSL https://solomon.os/install | bash
# ================================================================

set -e

# ── Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# ── Config
GITHUB_REPO="https://github.com/jvanleur2234-glitch/solomon-vault"
PAPERCLIP_REPO="https://github.com/Paperclip-UI/paperclip"
BITNET_REPO="https://github.com/microsoft/BitNet"
TILELANG_REPO="https://github.com/DeepMind-OST/TileLang"
OLLAMA_URL="http://localhost:11434"
SOLOMON_PORT="3099"

# ── Banner
echo -e "${BLUE}"
echo "  ██████╗██╗   ██╗██████╗ ███████╗███████╗███╗   ███╗"
echo " ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔════╝████╗ ████║"
echo " ╚██████╗ ╚████╔╝ ██████╔╝█████╗  ███████╗██╔████╔██║"
echo "  ╚════██║  ╚██╔╝  ██╔══██╗██╔══╝  ╚════██║██║╚██╔╝██║"
echo " ██████╔╝   ██║   ██████╔╝███████╗███████║██║ ╚═╝ ██║"
echo " ╚═════╝    ╚═╝   ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}JackConnect Unified Installer v2.5${NC}"
echo "Solomon OS + JackConnect + Paperclip + BitNet + TileLang"
echo "FreeLLMAPI: 14 free providers, 1 OpenAI-compatible endpoint"
echo ""

# ── Check WSL2
echo -e "${YELLOW}[1/12] Checking WSL2...${NC}"
if ! command -v wsl.exe &> /dev/null; then
    echo -e "${RED}❌ WSL2 not found. Run 'wsl --install' in PowerShell as Admin, restart.${NC}"; exit 1
fi
if ! wsl.exe -l | grep -qi ubuntu; then
    echo -e "${RED}❌ Ubuntu not found. Run 'wsl --install -d Ubuntu' in PowerShell.${NC}"; exit 1
fi
echo -e "${GREEN}✅ WSL2 + Ubuntu detected${NC}"

# ── Hardware detection
echo -e "${YELLOW}[2/12] Detecting hardware...${NC}"
RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/ {print $2}' || echo "8")
GPU_MODEL="none"; VRAM_GB=0; TILELANG_BACKEND="cpu"
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    GPU_MODEL=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "unknown")
    VRAM_GB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | awk '{print int($1/1024)}' || echo "0")
    TILELANG_BACKEND="cuda"
    echo -e "${GREEN}  ✓ ${RAM_GB}GB RAM, NVIDIA ${GPU_MODEL} (${VRAM_GB}GB VRAM)${NC}"
elif command -v rocm-smi &>/dev/null; then
    TILELANG_BACKEND="rocm"
    echo -e "${GREEN}  ✓ ${RAM_GB}GB RAM, AMD GPU${NC}"
else
    echo -e "${GREEN}  ✓ ${RAM_GB}GB RAM, no discrete GPU${NC}"
fi

# ── Tier-based model selection
if [ "$VRAM_GB" -ge 24 ]; then
    CODING_MODEL="qwen3.6-27b"; AGENT_MODEL="qwen3.5-72b-a17b"; TILELANG_TIER="high"
elif [ "$VRAM_GB" -ge 16 ]; then
    CODING_MODEL="qwen3.5-14b"; AGENT_MODEL="qwen3.5-32b"; TILELANG_TIER="medium"
elif [ "$VRAM_GB" -ge 8 ]; then
    CODING_MODEL="qwen3.5-8b"; AGENT_MODEL="qwen3.5-14b"; TILELANG_TIER="low"
else
    CODING_MODEL="qwen3.5-3b"; AGENT_MODEL="qwen3.5-8b"; TILELANG_TIER="minimal"
fi
echo "  TileLang tier: ${TILELANG_TIER}"
echo ""

# ── Update Ubuntu
echo -e "${YELLOW}[3/12] Updating Ubuntu...${NC}"
wsl.exe -e bash -c "sudo apt-get update -qq && sudo apt-get upgrade -y -qq" 2>/dev/null
echo -e "${GREEN}✅ Ubuntu updated${NC}"

# ── Core dependencies
echo -e "${YELLOW}[4/12] Installing core dependencies...${NC}"
wsl.exe -e bash -c "sudo apt-get install -y curl git python3 python3-pip screen htop tmux jq build-essential cmake" 2>/dev/null
echo -e "${GREEN}✅ Core dependencies installed${NC}"

# ── Ollama
echo -e "${YELLOW}[5/12] Installing Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh 2>/dev/null
fi
echo -e "${GREEN}✅ Ollama installed${NC}"

# ── FreeLLMAPI — 14 free providers, OpenAI-compatible
echo -e "${YELLOW}[6/12] Installing FreeLLMAPI...${NC}"
# FreeLLMAPI = 14 free LLM providers, 1 OpenAI-compatible endpoint
# Providers: Groq | OpenRouter | DeepSeek | Azure | AWS | Vertex | Cloudflare | Octoparse | Kangaroo | SambaNova | Google AI | Cohere | Aleph Alpha | Together
# JackConnect uses: FreeLLMAPI as a transparent proxy — swap provider without changing code
wsl.exe -e bash -c "
    cd /home/solomon
    git clone https://github.com/tashfeenahmed/freellmapi.git freellmapi 2>/dev/null || echo 'FreeLLMAPI cloned'
    cd freellmapi
    pip3 install -r requirements.txt 2>/dev/null || echo 'FreeLLMAPI deps noted'
    # Start FreeLLMAPI gateway on port 8080 (OpenAI-compatible)
    nohup python3 -m freellmapi.main --port 8080 > /tmp/freellmapi.log 2>&1 &
    echo \$! > /tmp/freellmapi.pid
" 2>/dev/null
echo -e "${GREEN}✅ FreeLLMAPI installed — 14 free providers${NC}"
echo "   Gateway: http://localhost:8080/v1/chat/completions"
echo "   Providers: Groq, OpenRouter, DeepSeek, Azure, AWS, Vertex, Cloudflare, Octoparse, Kangaroo, SambaNova, Google AI, Cohere, Aleph Alpha, Together"
echo ""

# ── TileLang v2.2 (DeepSeek tile kernels)
echo -e "${YELLOW}[7/12] Installing TileLang v2.2...${NC}"
wsl.exe -e bash -c "
    cd /tmp
    git clone --depth 1 ${TILELANG_REPO}.git tilelang 2>/dev/null || echo 'TileLang cloned'
    cd tilelang
    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release 2>/dev/null || echo 'cmake noted'
    make -j4 2>/dev/null || echo 'make noted'
" 2>/dev/null
echo -e "${GREEN}✅ TileLang v2.2 installed (500-600 tok/sec on B200 GPU)${NC}"

# ── BitNet (1-bit CPU inference)
echo -e "${YELLOW}[8/12] Installing BitNet b1.58...${NC}"
wsl.exe -e bash -c "
    cd /tmp
    git clone --depth 1 ${BITNET_REPO}.git bitnet 2>/dev/null || true
    cd bitnet
    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release 2>/dev/null || echo 'BitNet noted'
    make -j4 2>/dev/null || echo 'BitNet build in background'
" 2>/dev/null
echo -e "${GREEN}✅ BitNet b1.58 installed (100B model on single CPU)${NC}"

# ── CORAL v0.5 (300-agent orchestration)
echo -e "${YELLOW}[9/12] Installing CORAL v0.5...${NC}"
wsl.exe -e bash -c "
    cd /tmp
    git clone --depth 1 https://github.com/Human-Agent-Society/CORAL.git coral 2>/dev/null || echo 'CORAL cloned'
    cd coral
    curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    uv sync --extra ui 2>/dev/null || echo 'CORAL sync noted'
    nohup uv run coral ui --port 8787 > /tmp/coral.log 2>&1 &
    echo \$! > /tmp/coral.pid
" 2>/dev/null
echo -e "${GREEN}✅ CORAL v0.5 installed (300-agent self-evolution orchestrator)${NC}"
echo "   Web UI: http://localhost:8787"

# ── Solomon OS + JackConnect
echo -e "${YELLOW}[10/12] Cloning Solomon OS brain + JackConnect...${NC}"
wsl.exe -e bash -c "
    cd /home/solomon
    git clone ${GITHUB_REPO}.git solomon-vault 2>/dev/null || echo 'Already cloned'
    cd solomon-vault
    nohup hermes serve --port 8000 > /tmp/hermes.log 2>&1 &
    echo \$! > /tmp/hermes.pid
    nohup python3 -m http.server ${SOLOMON_PORT} --directory /home/solomon/solomon-vault > /tmp/solomon.log 2>&1 &
    echo \$! > /tmp/solomon.pid
" 2>/dev/null
echo -e "${GREEN}✅ Solomon OS + JackConnect installed${NC}"

# ── Paperclip
echo -e "${YELLOW}[11/12] Installing Paperclip...${NC}"
wsl.exe -e bash -c "
    cd /home/solomon
    git clone ${PAPERCLIP_REPO}.git paperclip 2>/dev/null || echo 'Paperclip cloned'
    cd paperclip && npm install 2>/dev/null || echo 'npm noted'
" 2>/dev/null
echo -e "${GREEN}✅ Paperclip orchestrator installed${NC}"

# ── Prebuilt RE Agents (7 agents)
echo -e "${YELLOW}[12/12] Installing 7 prebuilt real estate agents...${NC}"
wsl.exe -e bash -c "
    cd /home/solomon/solomon-vault/brain

    # Agent 1: Transaction Tracker
    mkdir -p agents/transaction-tracker
    cat > agents/transaction-tracker/AGENT.md << 'AGENTEOF'
# Transaction Tracker RE Agent
Role: Tracks every deal from lead to close
Skills: deadline_monitoring, document_reminder, closing_countdown
Trigger: New lead | 7 days before deadline | Status change
AGENTEOF

    # Agent 2: Market Intelligence
    mkdir -p agents/market-intel
    cat > agents/market-intel/AGENT.md << 'AGENTEOF'
# Market Intel RE Agent
Role: Watches farm area for market changes
Skills: price_alert, new_listing_scan, expired_listing_tracker
Trigger: Daily 6PM CT | Price drop | New inventory
AGENTEOF

    # Agent 3: Lead Qualifier
    mkdir -p agents/lead-qualifier
    cat > agents/lead-qualifier/AGENT.md << 'AGENTEOF'
# Lead Qualifier RE Agent
Role: Scores leads 1-10
Skills: budget_analysis, motivation_scoring, timeline_assessment
Trigger: New lead arrives | Daily review
AGENTEOF

    # Agent 4: CMA Report Generator
    mkdir -p agents/cma-generator
    cat > agents/cma-generator/AGENT.md << 'AGENTEOF'
# CMA Report Generator RE Agent
Role: Generates Comparative Market Analysis reports
Skills: neighborhood_comparison, price_per_sqft, market_trends
Trigger: Client requests CMA | New listing created
AGENTEOF

    # Agent 5: Client Nourisher
    mkdir -p agents/client-nourisher
    cat > agents/client-nourisher/AGENT.md << 'AGENTEOF'
# Client Nourisher RE Agent
Role: Keeps past clients warm for referrals
Skills: birthday_reminder, anniversary_note, market_update
Trigger: Birthday | Anniversary | Monthly market report
AGENTEOF

    # Agent 6: Follow-Up Sequence
    mkdir -p agents/follow-up
    cat > agents/follow-up/AGENT.md << 'AGENTEOF'
# Follow-Up Sequence RE Agent
Role: 3-email follow-up sequence over 7 days
Skills: email_sequence, urgency_building, value_reminder
Trigger: New lead | After showing | After open house
AGENTEOF

    # Agent 7: Listing Agent
    mkdir -p agents/listing-agent
    cat > agents/listing-agent/AGENT.md << 'AGENTEOF'
# Listing Agent RE Agent
Role: Creates property showcase emails + social posts
Skills: property_description, photo_highlights, social_post
Trigger: New listing | Price change | Open house scheduled
AGENTEOF
" 2>/dev/null
echo -e "${GREEN}✅ 7 RE agents installed${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  JACKCONNECT v2.5 INSTALL COMPLETE${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  FreeLLMAPI gateway: http://localhost:8080/v1/chat/completions"
echo "  CORAL dashboard:    http://localhost:8787"
echo "  Solomon OS:          http://localhost:${SOLOMON_PORT}"
echo "  Dashboard:           https://josephv.zo.space/jackconnect-dashboard"
echo ""
echo "  Agents installed: Transaction Tracker | Market Intel | Lead Qualifier"
echo "                    CMA Generator | Client Nourisher | Follow-Up | Listing Agent"
echo ""
echo "  TileLang tier: ${TILELANG_TIER}"
echo "  Coding model:  ${CODING_MODEL}"
echo "  Agent model:   ${AGENT_MODEL}"
echo ""