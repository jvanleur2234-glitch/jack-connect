# JackConnect + Cabinet — Integration Spec

**Date:** 2026-04-17
**Purpose:** Integrate Cabinet as the brain and orchestration layer for JackConnect real estate AI agents.

---

## What This Builds

Cabinet replaces:
- Jack's scattered brain files (context, notes, CRM data)
- Manual cron agents (daily briefings, market intel loops)
- Watch Once's memory system
- The daily briefing Python scripts

Cabinet adds:
- Git-backed version history on every file
- AI agents that work while Jack sleeps
- Kanban mission boards
- Scheduled agent heartbeats (cron jobs)
- Embedded HTML apps (CMA builder, market dashboard)

---

## Architecture

```
JackConnect + Cabinet
├── cabinet/                      ← Cabinet app (Node.js)
│   ├── src/lib/agents/library/
│   │   ├── superintendent-re/     ← Jack's daily coordinator
│   │   ├── prospector-re/         ← Lead qualification
│   │   ├── property-matchmaker-re/← Buyer/seller matching
│   │   ├── investment-analyst-re/ ← CMA + rental analysis
│   │   ├── transaction-coordinator-re/ ← Deal tracking
│   │   ├── client-nourisher-re/  ← SOI nurturing
│   │   └── market-intel-re/      ← Farm area monitoring
│   └── data/
│       └── alpine-real-estate/   ← Jack's KB workspace
│           ├── prospecting/
│           ├── matchmaking/
│           ├── investment-analysis/
│           ├── transactions/
│           ├── nourish/
│           ├── market-intel/
│           ├── context/           ← Jack's bio, goals, farm area
│           └── apps/              ← Embedded HTML tools
│               ├── cma-builder/   ← CMA report generator
│               ├── daily-briefing/← Morning briefing display
│               └── watch-once/   ← Workflow capture UI
├── automate-scripts/             ← autoMate scripts for desktop
│   └── real-estate/
│       ├── cma-from-mls.md
│       ├── lead-crm-entry.md
│       └── send-market-update.md
├── solomon-skills/               ← JackConnect skill library
│   ├── real-estate-cma/
│   ├── lead-qualifier/
│   ├── market-intel/
│   ├── client-nourisher/
│   ├── invoice-generator/
│   └── transaction-tracker/
└── pashov-skills-reference/      ← SKILL.md format reference
```

---

## How It Works For Jack

### Day 1 — Setup
```bash
# On Jack's machine (Linux/Mac):
curl -sSL https://solomon.os/install | bash -s cabinet

# Cabinet installer asks 5 questions:
# 1. What's your name? → Jack Vanleur
# 2. What's your brokerage? → Alpine Real Estate Companies
# 3. What's your farm area? → Sioux Falls, SD (neighborhoods/ZIPs)
# 4. What's your typical price range? → $200K-$500K
# 5. Who are your first clients? → [import from CRM or enter manually]

# Installer:
# 1. Installs Cabinet (Node.js)
# 2. Clones JackConnect workspace
# 3. Populates Jack's context/ with his bio and goals
# 4. Activates all 7 real estate agents
# 5. Sets up daily heartbeat schedule
# 6. Starts Cabinet daemon

# Jack opens browser → http://localhost:3000
# → Sees his KB with all agents active
```

### Every Morning — 7 AM CT
1. Cabinet daemon fires **Superintendent RE** heartbeat
2. Superintendent reads: today's transactions, hot leads, market alerts, nurturing calendar
3. Superintendent generates the daily briefing → saves to `/alpine-real-estate/daily-briefing/YYYY-MM-DD.md`
4. Jack opens Cabinet → sees briefing on home screen
5. Jack reads: top 3 actions for the day

### Every Time a Lead Comes In
1. Jack or a referral source gives him a lead
2. **Prospector RE** gets assigned the lead
3. Prospector researches, scores 1-10, drafts outreach
4. Jack reviews in Cabinet → approves or edits outreach
5. Jack sends the outreach

### Every Time Jack Does Something New
1. Jack does the task manually once
2. **Watch Once** captures the workflow
3. Superintendent analyzes: can this be automated?
4. If yes → generates an autoMate script → saves to `/automate-scripts/`
5. Next time → autoMate runs it automatically

---

## The 7 Real Estate Agents

### 1. Superintendent RE (Lead Agent)
- **Wakes up:** 7 AM CT daily
- **Does:** Generates the morning briefing
- **Coordinates:** All other agents
- **Escalates:** Critical issues to Jack via Telegram

### 2. Prospector RE
- **Wakes up:** Every 4 hours, Monday-Friday
- **Does:** Finds leads, scores them 1-10, drafts outreach
- **Files:** `/prospecting/leads/`, `/prospecting/outreach/`

### 3. Property Matchmaker RE
- **Wakes up:** 6 AM CT daily
- **Does:** Matches buyers to properties, calculates commissions
- **Files:** `/matchmaking/buyer-matches/`, `/matchmaking/seller-matches/`

### 4. Investment Analyst RE
- **Wakes up:** 8 AM CT daily
- **Does:** CMA reports, rental analyses, cap rates
- **Files:** `/investment-analysis/cma-reports/`, `/investment-analysis/rental-analyses/`

### 5. Transaction Coordinator RE
- **Wakes up:** 7 AM CT daily
- **Does:** Tracks deadlines, contingencies, signatures
- **Files:** `/transactions/[address]/tracking.md`

### 6. Client Nourisher RE
- **Wakes up:** 9 AM CT daily (every day)
- **Does:** Birthday texts, anniversaries, market updates, referrals
- **Files:** `/nourish/contacts/`, `/nourish/outreach/`

### 7. Market Intelligence RE
- **Wakes up:** Every 6 hours, Monday-Friday
- **Does:** New listings, price drops, expired FSBO alerts
- **Files:** `/market-intel/daily-alerts/`, `/market-intel/monthly-reports/`

---

## autoMate Script Integration

autoMate scripts live in `~/.automate/scripts/` (user's home directory).

When a Watch Once workflow is captured:
1. Superintendent analyzes the workflow
2. Writes the autoMate script to the workspace
3. When Jack says "do that task again" → autoMate runs the script
4. autoMate opens the app, does the clicks, saves the result

Example: Jack does a CMA in MLS manually.
1. Watch Once captures: MLS → search → comps → screenshot → paste to CMA template → email to client
2. Superintendent writes: `cma-from-mls.md` script
3. Next time: "Run CMA for [address]" → autoMate executes the script
4. Jack reviews → sends the email

---

## Embedded HTML Apps

These live inside Cabinet as `/apps/[app-name]/index.html`.

### CMA Builder (`/apps/cma-builder/`)
- Form to enter property address
- Pulls comps from MLS (or manual entry)
- Generates formatted CMA report
- Download as PDF or copy to clipboard

### Daily Briefing (`/apps/daily-briefing/`)
- Shows today's briefing in a clean card UI
- One-click actions: call lead, schedule showing, send email
- Market pulse widget

### Watch Once (`/apps/watch-once/`)
- Start/stop recording button
- Shows captured workflow steps
- "Save as automation" button → generates autoMate script

---

## Data Flow

```
Lead enters system
       ↓
Prospector RE scores + qualifies
       ↓
Jack approves outreach
       ↓
Property Matchmaker RE finds matches
       ↓
Investment Analyst RE runs CMA
       ↓
Transaction Coordinator RE tracks deal
       ↓
Client Nourisher RE keeps SOI warm
       ↓
Market Intelligence RE monitors farm area
       ↓
Superintendent RE coordinates all of the above
       ↓
Jack gets daily briefing with everything
```

---

## Cabinet as Jack's Knowledge Base

Everything Jack knows lives in Cabinet:

```
/context/
  jack-bio.md          ← Jack's story, goals, bio
  farm-area.md         ← Neighborhoods, ZIPs, price ranges
  brokerage-info.md    ← Alpine Real Estate details, commission splits
  clients/             ← Past client profiles, transaction history
  deals/               ← Closed deals with notes and lessons learned
  preferences.md       ← How Jack likes to communicate, when he works
```

---

## Setup Commands

```bash
# 1. Install Cabinet
npx create-cabinet@latest alpine-real-estate
cd alpine-real-estate

# 2. Copy real estate agent templates
cp -r /home/workspace/jack-connect/cabinet/src/lib/agents/library/prospector-re \
      cabinet/src/lib/agents/library/
# ... repeat for all 7 agents

# 3. Initialize the workspace
mkdir -p data/alpine-real-estate/{prospecting,matchmaking,investment-analysis,transactions,nourish,market-intel,context,apps}

# 4. Create Jack's context
cp /home/workspace/jack-connect/solomon-skills/real-estate-cma/skills/real-estate-cma.md \
   data/alpine-real-estate/context/jack-bio.md

# 5. Start Cabinet
npm run dev:all

# 6. Connect to Telegram for alerts
# (Cabinet → Settings → Notifications → Telegram)
```

---

## JackConnect Skills → Cabinet Agents

| JackConnect Skill | Cabinet Agent | Skill File |
|------------------|---------------|------------|
| `real-estate-cma` | Investment Analyst RE | `investment-analysis/cma-reports/` |
| `lead-qualifier` | Prospector RE | `prospecting/leads/` |
| `market-intel` | Market Intelligence RE | `market-intel/daily-alerts/` |
| `client-nourisher` | Client Nourisher RE | `nourish/contacts/` |
| `invoice-generator` | (standalone skill) | `context/invoices/` |
| `transaction-tracker` | Transaction Coordinator RE | `transactions/` |

---

## Comparison: Before vs. After

| Before (JackConnect v1) | After (JackConnect + Cabinet) |
|------------------------|------------------------------|
| Brain files scattered in markdown | Central KB, git-backed, searchable |
| Daily briefing via Python script | AI agent generates + schedules itself |
| Watch Once = capture only | Watch Once → autoMate script + agent learns |
| 7 agents = separate scripts | 7 agents = Cabinet agents with memory + scheduling |
| No version history | Full git diff/restore on everything |
| Separate zo.space pages | Embedded HTML apps inside the KB |
| Manual cron jobs | Native Cabinet heartbeat scheduling |

---

## Next Steps

1. [ ] Deploy Cabinet locally on Jack's machine (Mac/Linux)
2. [ ] Populate Jack's context/ folder with his real data
3. [ ] Connect Telegram for Superintendent alerts
4. [ ] Test the daily briefing heartbeat
5. [ ] Run Prospector RE on a real lead
6. [ ] Build the CMA Builder embedded app
7. [ ] Wire Watch Once → autoMate → Cabinet agent loop
8. [ ] Get Jack's first testimonial

---

*Built for Jack Vanleur | Alpine Real Estate Companies*
*Powered by Solomon OS*
