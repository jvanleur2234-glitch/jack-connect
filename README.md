# Solomon Companion — AI Agent Suite for Real Estate
**Jack Vanleur | Alpine Real Estate Companies**

> **One-click setup. Watch once, automate forever.**
> Your AI team installs itself, explains what it does, and upgrades on command.

---

## What Is This?

Your personal AI team that:
1. **Installs itself** — one command, fully automatic
2. **Watches what you do** — learns your workflows by watching screen once
3. **Explains itself** — tells you what each upgrade does for YOUR business
4. **Upgrades on command** — superintendent asks, you say yes or no
5. **Never stops improving** — learns every action, builds skills automatically

---

## The Upgrade Stack

| Tier | Price | Models | Best For |
|------|-------|--------|----------|
| **Solo** | Free | qwen3:1.7b + faster-whisper + piper | Learning, testing |
| **Pro** | $30/mo | qwen3:14b + faster-whisper-small + elevenlabs | Real estate agents, 5-10 tasks/day |
| **Business** | $100/mo | qwen3:32b + faster-whisper-medium + elevenlabs | Teams, 20-50 tasks/day |
| **Enterprise** | Custom | claude-sonnet-4 + AssemblyAI + elevenlabs | Large teams, mission-critical |

### What Each Upgrade Does For You (Real Estate Specific)

**Solo → Pro ($30/mo):**
- CMA reports that actually compare neighborhoods, not just squares
- Lead qualification that reads between the lines of what buyers say vs mean
- Contract analysis that spots unusual terms before you miss them
- 3x faster on long documents

**Pro → Business ($100/mo):**
- Full investment analysis on rental properties in seconds
- Multiple client coordination without dropping balls
- Automated follow-up sequences that feel personal
- Handles 4x more volume without losing quality

**Business → Enterprise (Custom):**
- Everything at enterprise scale
- Compliance-ready audit trails
- Multi-agent coordination for大型 transactions
- Dedicated support

---

## Quick Start (One Command)

```bash
# Full auto-install for Solo tier (free)
curl -sSL https://solomon.os/install | bash

# Pro tier
curl -sSL https://solomon.os/install | bash -s pro

# Business tier
curl -sSL https://solomon.os/install | bash -s business
```

The installer:
1. Checks your system (Linux/Mac/Windows support)
2. Installs Ollama + faster-whisper + piper (all free, local)
3. Downloads the right model for your tier
4. Sets up Solomon OS with your business profile
5. Starts the superintendent
6. Sends you a Telegram message: "I'm set up and ready. Here's what I can do for you, Jack."

---

## Your AI Team (7 Agents)

### 🤖 Superintendent
Your single point of contact. Every morning at 7 AM CT you get:
- Today's priorities
- Hot leads that need attention NOW
- Your full deal pipeline
- Market updates from your farm area

**Commands:** Just text Telegram. Superintendent handles the rest.

### 📋 Prospector RE
Finds and qualifies leads 24/7. Scores each lead 1-10 and tells you exactly what to say.

### 🏠 Property Matchmaker RE
Matches buyers to properties automatically. Shows you matches with your commission.

### 📊 Investment Analyst RE
CMA, rental income analysis, cap rate, cash-on-cash return. Numbers in seconds.

### 📅 Transaction Coordinator RE
Tracks every deadline, contingency, and signature. Never miss a closing date.

### 💬 Client Nourisher RE
Birthday texts, anniversary notes, market updates. Keeps your SOI warm year-round.

### 📈 Market Intelligence RE
Watches your farm area. Alerts you when listings expire, prices drop, or new inventory hits.

---

## Watch Once Automation

**The killer feature.** Here's how it works:

1. You do a task manually (once)
2. Watch Once captures your screen + what you did
3. Solomon OS analyzes: can this be automated?
4. If yes → asks "Want me to automate this?"
5. You say YES → skill is created and deployed
6. Next time → your AI does it automatically

**Example:** Jack sends a CMA report to a buyer client.
1. Jack manually creates the CMA in MLS
2. Watches once → uploads to Solomon OS
3. Analysis: "CMA report generation, can automate"
4. Next time → Superintendent asks "Ready to run the CMA for buyer client?"
5. Jack says YES → AI generates and sends the CMA

---

## Cross-Platform

| Platform | Status | Install |
|----------|--------|---------|
| macOS | ✅ Full | `curl -sSL https://solomon.os/install \| bash` |
| Linux | ✅ Full | `curl -sSL https://solomon.os/install \| bash` |
| Windows (WSL) | ✅ Full | Install WSL2, then same command |
| iOS/Android | 🔜 Roadmap | Tablet companion app Q3 2026 |
| ChromeOS | 🔜 Roadmap | Chromebook support Q4 2026 |

---

## Architecture

```
Solomon Companion (local, your machine)
├── Ollama (LLM, local inference)
│   └── qwen3:1.7b → 32b depending on tier
├── faster-whisper (STT, local)
│   └── Systran/tiny → medium depending on tier
├── piper-tts (TTS, local)
│   └── amy voice
├── MSS (screen capture, cross-platform)
└── Solomon OS API (cloud sync)
    ├── Watch Once Engine
    ├── Skill Builder
    ├── Upgrade Advisor
    └── Telegram (Superintendent)
```

---

## Files In This Project

```
jack-connect/
├── README.md                    ← You are here
├── SOLOMON_OS_GTM.md           ← Full business plan + pricing
├── daily-briefing/
│   ├── briefing.py             ← Daily briefing generator
│   └── data/
│       └── jack_vanleur.json   ← Jack's CRM data
├── solomon-companion/
│   ├── core.py                 ← Core engine (Ollama + Whisper + Piper + MSS)
│   └── src/
│       └── solomon-companion.sh # Cross-platform launcher
├── watch-once/
│   ├── server.py               ← Watch Once API server
│   └── protocol.md             ← Protocol spec
└── SPEC.md                     ← This file
```

---

## Next Steps

1. **Test the briefing generator:**
   ```bash
   python3 daily-briefing/briefing.py
   ```

2. **Start Solomon Companion:**
   ```bash
   python3 solomon-companion/core.py
   ```

3. **Ask the superintendent anything via Telegram**

---

*Built with Solomon OS — Joseph's autonomous AI business system*
*Last updated: April 11, 2026*