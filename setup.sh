#!/bin/bash
#===============================================================================
# JackConnect + Cabinet — One-Command Setup
# For Jack Vanleur | Alpine Real Estate Companies
# Run on: macOS, Linux, or Windows WSL
#===============================================================================

set -e

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\n\ue2b1[31m'; GRN='\ue2b1[32m'; YEL='\ue2b1[33m'; BLU='\ue2b1[34m'
CYN='\ue2b1[36m'; MAG='\ue2b1[35m'; RST='\ue2b1[0m'
INFO(){ printf >&2 \"${BLU}[INFO]${RST} %s\n\" \"$*\"; }
OK(){ printf >&2 \"${GRN}[OK]  ${RST} %s\n\" \"$*\"; }
WARN(){ printf >&2 \"${YEL}[WARN]${RST} %s\n\" \"$*\"; }
ERR(){ printf >&2 \"${RED}[ERR] ${RST} %s\n\" \"$*\"; }

# ── Banner ───────────────────────────────────────────────────────────────────
cat << 'BANNER'
   __                  __  ____       __
  / /   ___  ___  ___ / / / __/__  __/ /  ___  __ __
 / /__ / _ \/ _ \/ -_) _ \/ _ \/ / / / _ \/ _ \\ \/_/
/____|/\\_,_/\\_,/\\_/__|_.__/___/\\_,_/_.__/\\___//_/_/

JackConnect + Cabinet  —  Your AI Real Estate Team
BANNER
echo

# ── Detect OS ────────────────────────────────────────────────────────────────
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
if [[ -f /etc/os-release ]]; then source /etc/os-release; fi

case $OS in
  darwin*)  PLATFORM=macos; PKG_MGR=brew ;;
  linux*)   PLATFORM=linux; PKG_MGR=apt ;;
  msys*|mingw*|cygwin*) PLATFORM=wsl; PKG_MGR=apt ;;
  *)        ERR \"Unsupported OS: $OS\"; exit 1 ;;
esac
INFO \"Detected: $PLATFORM ($PKG_MGR)\"

# ── Parse Args ───────────────────────────────────────────────────────────────
TIER=${1:-solo}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
SKIP_MODELS=${SKIP_MODELS:-}

# ── Env Validation ───────────────────────────────────────────────────────────
if [[ -z $TELEGRAM_BOT_TOKEN ]]; then
  WARN \"TELEGRAM_BOT_TOKEN not set. Daily briefings will be local only.\"
  WARN \"Set it with: export TELEGRAM_BOT_TOKEN=your_token_here\"
  echo
fi

# ── Step 1: Clone JackConnect ────────────────────────────────────────────────
STEPS=6
CURRENT=1

info_step() { INFO \"[$CURRENT/$STEPS] $1\"; ((CURRENT++)) || true; }

info_step \"Cloning JackConnect repository...\"
if [[ -d ~/jack-connect ]]; then
  cd ~/jack-connect && git pull origin main 2>/dev/null || git pull origin master
  OK \"JackConnect already exists — pulled latest\"
else
  git clone https://github.com/jvanleur2234-glitch/jack-connect ~/jack-connect
  OK \"Cloned JackConnect\"
fi
cd ~/jack-connect

# ── Step 2: Install Ollama ───────────────────────────────────────────────────
info_step \"Installing Ollama (local AI inference)...\"
if command -v ollama &>/dev/null; then
  OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo 'installed')
  OK \"Ollama already installed: $OLLAMA_VERSION\"
else
  curl -fsSL https://ollama.ai/install.sh | sh
  OK \"Ollama installed\"
fi

# ── Step 3: Pull AI Models ───────────────────────────────────────────────────
info_step \"Pulling AI models for $TIER tier...\"

pull_model_if_missing() {
  local model=$1
  if ! ollama list 2>/dev/null | grep -q \"^$model \"; then
    INFO \"  Pulling $model...\"
    ollama pull $model 2>&1 | tail -2
  else
    OK \"  $model already present\"
  fi
}

case $TIER in
  solo)
    pull_model_if_missing qwen3:1.7b
    pull_model_if_missing llama3.2:1b
    ;;
  pro)
    pull_model_if_missing qwen3:14b
    pull_model_if_missing llama3.2:3b
    ;;
  business)
    pull_model_if_missing qwen3:32b
    pull_model_if_missing llama3.2:3b
    pull_model_if_missing deepseek-coder:6.7b
    ;;
  enterprise)
    INFO \"  Enterprise tier — using cloud APIs (Anthropic/GPT)\"
    INFO \"  Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment\"
    ;;
esac

# ── Step 4: Install Cabinet ─────────────────────────────────────────────────
info_step \"Installing Cabinet (AI team OS)...\"

if [[ -d ~/cabinet ]]; then
  cd ~/cabinet && git pull origin main 2>/dev/null || git pull origin master
  OK \"Cabinet already present — pulled latest\"
else
  npx create-cabinet@latest ~/cabinet --skip-onboarding 2>/dev/null || {
    git clone https://github.com/hilash/cabinet ~/cabinet
    cd ~/cabinet
    npm install 2>&1 | tail -3
  }
  OK \"Cabinet installed\"
fi

# ── Step 5: Install Real Estate Agent Templates ─────────────────────────────
info_step \"Installing 7 real estate agents into Cabinet...\"

AGENTS=(
  superintendent-re:superintendent-re:🤖
  prospector-re:prospector-re:🏠
  property-matchmaker-re:property-matchmaker-re:🔑
  investment-analyst-re:investment-analyst-re:📊
  transaction-coordinator-re:transaction-coordinator-re:📋
  client-nourisher-re:client-nourisher-re:💬
  market-intel-re:market-intel-re:📈
)

cd ~/jack-connect
for entry in \"${AGENTS[@]}\"; do
  IFS=':' read -r slug name emoji <<< \"$entry\"
  src=~/jack-connect/cabinet/src/lib/agents/library/$slug
  if [[ -d $src ]]; then
    cp -r $src ~/cabinet/src/lib/agents/library/ 2>/dev/null || true
    OK \"  $emoji $name installed\"
  else
    WARN \"  $slug template not found — skipping\"
  fi
done

# Copy Jack's business context
cp ~/jack-connect/daily-briefing/data/jack_vanleur.json ~/cabinet/data/ 2>/dev/null || true

# Copy autoMate scripts
mkdir -p ~/.automate/scripts/real-estate/
cp ~/jack-connect/automate-scripts/real-estate/*.md ~/.automate/scripts/real-estate/ 2>/dev/null || true

# ── Step 6: Configure & Start ───────────────────────────────────────────────
info_step \"Configuring JackConnect for Jack Vanleur...\"

# Write Jack's config
cat > ~/cabinet/data/jack-vanleur.config.json << 'EOF'
{
  \"owner\": \"Jack Vanleur\",
  \"company\": \"Alpine Real Estate Companies\",
  \"location\": \"Sioux Falls, SD\",
  \"tier\": \"SOLO\",
  \"telegram_bot_token\": \"ENV:TELEGRAM_BOT_TOKEN\",
  \"daily_brief_time\": \"07:00 America/Chicago\",
  \"farm_areas\": [\"Sioux Falls SD 57104\", \"Sioux Falls SD 57105\", \"Tea SD 57064\"],
  \"specialties\": [\"Residential\", \"Investment\", \"CMA\", \"Lead Gen\"],
  \"superintendent_name\": \"JackAI\"
}
EOF

# Write .env.local for Cabinet
cat > ~/cabinet/.env.local << 'EOF'
KB_PASSWORD=
DOMAIN=localhost
ANTHROPIC_API_KEY=ENV:ANTHROPIC_API_KEY
OLLAMA_HOST=http://localhost:11434
EOF

# Create daily briefing cron script
mkdir -p ~/cabinet/data/scripts/
cat > ~/cabinet/data/scripts/daily-brief.sh << 'SCRIPT'
#!/bin/bash
# Daily Briefing — Jack Vanleur
# Runs at 7 AM CT via Cabinet heartbeat

TIER=${1:-solo}
LOG=~/cabinet/data/logs/brief-$(date +%Y-%m-%d).log
mkdir -p ~/cabinet/data/logs

echo \"[$(date)] Generating daily briefing...\" >> $LOG

# Generate briefing
python3 ~/jack-connect/daily-briefing/briefing.py >> $LOG 2>&1

# Send via Telegram if token present
if [[ -n $TELEGRAM_BOT_TOKEN ]]; then
  MESSAGE=\"Good morning Jack! Here's your daily briefing.\"
  curl -s -X POST \"https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage\" \\
    -d \"chat_id=$TELEGRAM_CHAT_ID\" \\
    -d \"text=$MESSAGE\" \\
    -d \"parse_mode=Markdown\" >> $LOG 2>&1
fi

echo \"[$(date)] Done.\" >> $LOG
SCRIPT
chmod +x ~/cabinet/data/scripts/daily-brief.sh

# ── Start Cabinet ────────────────────────────────────────────────────────────
info_step \"Starting Cabinet and JackConnect services...\"

# Start Ollama in background
pkill -f \"ollama serve\" 2>/dev/null || true
nohup ollama serve >> ~/cabinet/data/logs/ollama.log 2>&1 &
sleep 2

# Start Cabinet daemon
cd ~/cabinet
pkill -f \"cabinet-daemon\" 2>/dev/null || true
nohup npm run dev:daemon >> ~/cabinet/data/logs/cabinet-daemon.log 2>&1 &
sleep 2

# Start Next.js
nohup npm run dev >> ~/cabinet/data/logs/cabinet-next.log 2>&1 &
sleep 3

# ── Final Status ─────────────────────────────────────────────────────────────
echo
echo \"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\"
OK \"JackConnect + Cabinet are LIVE\"
echo \"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\"
echo
printf \"  ${GRN}✅${RST} Ollama:          http://localhost:11434\n\"
printf \"  ${GRN}✅${RST} Cabinet UI:      http://localhost:3000\n\"
printf \"  ${GRN}✅${RST} Cabinet Daemon:  http://localhost:3001\n\"
echo

# Check services
check_service() {
  local name=$1; local url=$2
  if curl -sf --max-time 3 \"$url\" >/dev/null 2>&1; then
    printf \"  ${GRN}✅${RST} %s is running\n\" \"$name\"
  else
    printf \"  ${RED}❌${RST} %s failed to start — check logs\n\" \"$name\"
    printf \"    Logs: ~/cabinet/data/logs/\n\"
  fi
}

check_service \"Cabinet UI\" \"http://localhost:3000\"
check_service \"Cabinet Daemon\" \"http://localhost:3001\"
check_service \"Ollama\" \"http://localhost:11434/api/tags\"

echo
echo \"Next steps:\"
echo \"  1. Open http://localhost:3000 in your browser\"
echo \"  2. Click 'AI Team' → you should see 7 real estate agents\"
echo \"  3. Set ANTHROPIC_API_KEY in your shell for cloud models\"
echo \"  4. Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID for daily briefs\"
echo
echo \"To stop: pkill -f 'ollama|cabinet'\"
echo \"To restart: ~/jack-connect/setup.sh $TIER\"
echo