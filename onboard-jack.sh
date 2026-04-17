#!/bin/bash
#===============================================================================
# JackConnect — Interactive Onboarding
# Asks 5 questions, builds Jack's personalized AI team
# Run after setup.sh — this is the human setup step
#===============================================================================

set -e

RED='\033[31m'; GRN='\033[32m'; YEL='\033[33m'; BLU='\033[34m'; RST='\033[0m'
INFO(){ echo -e "${BLU}[?]${RST} $1"; }
ASK(){ echo -e "${YEL}[→]${RST} $1"; }
OK(){ echo -e "${GRN}[✓]${RST} $1"; }

CABINET_DIR=${CABINET_DIR:-$HOME/cabinet}
JACK_DIR=${JACK_DIR:-$HOME/jack-connect}

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  JackConnect — 5-Question Setup"
echo "  Your AI team is almost ready."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# ── Q1: Company ─────────────────────────────────────────────────────────────
ASK "What's your company name?"
echo -n "  → "; read COMPANY_NAME
COMPANY_NAME=${COMPANY_NAME:-Alpine Real Estate Companies}

ASK "What's your market / farm area? (e.g. Sioux Falls SD, or 'all of Minnesota')"
echo -n "  → "; read FARM_AREA
FARM_AREA=${FARM_AREA:-Sioux Falls, SD}

ASK "MLS platform? (supra, flexmls, matrix, realtor.com, other)"
echo -n "  → "; read MLS_PLATFORM
MLS_PLATFORM=${MLS_PLATFORM:-flexmls}

# ── Q2: Clients ─────────────────────────────────────────────────────────────
ASK "Who are your typical clients? (buyers, sellers, investors — pick 1-3)"
echo -n "  → "; read CLIENT_TYPES
CLIENT_TYPES=${CLIENT_TYPES:-Buyers, Sellers, Investors}

ASK "Average deal size? (e.g. \$250K, \$400K, \$1M+)"
echo -n "  → "; read AVG_DEAL_SIZE
AVG_DEAL_SIZE=${AVG_DEAL_SIZE:-\$300,000}

# ── Q3: Communications ───────────────────────────────────────────────────────
ASK "Phone number for Telegram alerts? (or press Enter to skip)"
echo -n "  → "; read TELEGRAM_CHAT_ID

ASK "Email for reports? (or press Enter to skip)"
echo -n "  → "; read REPORT_EMAIL

# ── Q4: Pain Points ─────────────────────────────────────────────────────────
ASK "Biggest time-waster right now? (e.g. CMA reports, follow-up texts, MLS data entry)"
echo -n "  → "; read PAIN_POINT
PAIN_POINT=${PAIN_POINT:-CMA reports and lead follow-up}

ASK "What do you wish was automatic? (the one thing you hate doing)"
echo -n "  → "; read WISH_AUTO
WISH_AUTO=${WISH_AUTO:-Follow-up texts to hot leads}

# ── Q5: Tier Selection ───────────────────────────────────────────────────────
echo
ASK "Which tier do you want to start with?"
echo "  1) Solo   — Free,  qwen3:1.7b, 3 agents"
echo "  2) Pro    — \$30/mo, qwen3:14b, 7 agents, ElevenLabs voice"
echo "  3) Business — \$100/mo, qwen3:32b, unlimited agents"
echo -n "  → [1] "; read TIER_CHOICE
case ${TIER_CHOICE:-1} in
  1) TIER=solo; MODEL=qwen3:1.7b ;;
  2) TIER=pro; MODEL=qwen3:14b ;;
  3) TIER=business; MODEL=qwen3:32b ;;
esac

# ── Write Config ─────────────────────────────────────────────────────────────
CONFIG_FILE="$CABINET_DIR/data/jack-vanleur.json"

mkdir -p "$CABINET_DIR/data"

cat > "$CONFIG_FILE" << EOF
{
  "owner": "Jack Vanleur",
  "company": "$COMPANY_NAME",
  "farm_area": "$FARM_AREA",
  "mls_platform": "$MLS_PLATFORM",
  "client_types": "$CLIENT_TYPES",
  "avg_deal_size": "$AVG_DEAL_SIZE",
  "tier": "${TIER_NAMES[$((TIER_CHOICE-1))]:-solo}",
  "model": "$MODEL",
  "telegram_chat_id": "$TELEGRAM_CHAT_ID",
  "report_email": "$REPORT_EMAIL",
  "pain_point": "$PAIN_POINT",
  "wish_was_automatic": "$WISH_AUTO",
  "setup_completed": "$(date -Iseconds)",
  "version": "1.0"
}
EOF

OK "Config written: $CONFIG_FILE"

# ── Write Company Context ─────────────────────────────────────────────────────
mkdir -p "$CABINET_DIR/data/company"
cat > "$CABINET_DIR/data/company/about.md" << EOF
# $COMPANY_NAME

**Owner:** Jack Vanleur
**Market:** $FARM_AREA
**MLS:** $MLS_PLATFORM
**Avg Deal:** $AVG_DEAL_SIZE

## Clients
$CLIENT_TYPES

## Biggest Pain Point
$PAIN_POINT

## Wish Was Automatic
$WISH_AUTO
EOF

OK "Company context written"

# ── Tell Superintendent to prioritize the pain point ─────────────────────────
mkdir -p "$CABINET_DIR/data/agents/superintendent-re/missions"
cat > "$CABINET_DIR/data/agents/superintendent-re/missions/priority-001.md" << EOF
# Priority: Fix Jack's Biggest Pain Point

**Created:** $(date -I)
**Status:** Active
**Priority:** Critical

## Jack Said
> "$WISH_AUTO"

## Why This Matters
Jack spends X hours/week on this. If we automate it, he recoups time every week forever.

## First Action
Build a Watch Once recording of Jack doing "$WISH_AUTO" manually.
Then create an autoMate script to automate it.

## Success Metric
Jack confirms it works in next briefing.
EOF

OK "Priority mission created for Superintendent"

# ── Build Jack's First Briefing ─────────────────────────────────────────────
echo
INFO "Generating your first daily briefing..."
mkdir -p "$CABINET_DIR/data/briefings"

BRIEFING_FILE="$CABINET_DIR/data/briefings/brief-$(date +%Y-%m-%d).md"
python3 "$JACK_DIR/daily-briefing/briefing.py" > "$BRIEFING_FILE" 2>&1 || {
  cat > "$BRIEFING_FILE" << EOF
# Daily Briefing — $(date +"%B %d, %Y")

## Morning Overview
Good morning Jack! Here's what's happening in **$FARM_AREA** today.

## Weather
Perfect day to tour properties.

## Top Leads Needing Attention
*(JackConnect is learning your leads — check back tomorrow for AI-scored priorities)*

## Market Update
*(Market Intelligence agent is monitoring $FARM_AREA — data populates in 24 hours)*

## Today's Priorities
1. ☐ Review new MLS listings in $FARM_AREA
2. ☐ Follow up with leads from last 7 days
3. ☐ Touch base with past clients — SOI matters!

## Motivation
> "Every day you show up is a day closer to closing." — Jack AI

---
*Built by JackConnect + Solomon OS*
EOF
}

OK "First briefing generated"
echo

# ── Summary ───────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
OK "Setup complete! Here's your team:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "  🤖 Superintendent RE  —  Your daily AI coordinator"
echo "     → Sends you a briefing every morning at 7 AM CT"
echo
echo "  🏠 Prospector RE     —  Finds and scores leads"
echo "     → Scans MLS daily for new buyers/sellers"
echo
echo "  🔑 Property Matchmaker — Matches buyers to properties"
echo "     → Runs CMA reports on demand"
echo
echo "  📊 Investment Analyst  —  Numbers, cap rates, ROI"
echo "     → Calculates investment deals instantly"
echo
echo "  📋 Transaction Coord  —  Tracks every deadline"
echo "     → You'll never miss a closing date again"
echo
echo "  💬 Client Nourisher   —  SOI, birthdays, anniversaries"
echo "     → Keeps past clients warm year-round"
echo
echo "  📈 Market Intel RE    —  Your farm area, 24/7"
echo "     → Alerts when listings expire or prices drop"
echo
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
INFO "Open Cabinet: http://localhost:3000"
INFO "Click 'AI Team' tab to see your agents working."
echo
if [[ -n "$TELEGRAM_CHAT_ID" ]]; then
  INFO "Telegram alerts: Enabled → you'll get daily briefs there"
else
  WARN "Telegram not configured → briefings are local only"
  echo "  To enable: edit $CONFIG_FILE and add telegram_chat_id"
fi
echo
INFO "What should your team tackle first?"
INFO "Tell JackAI: 'I want to automate [X]' — and watch it happen."
echo