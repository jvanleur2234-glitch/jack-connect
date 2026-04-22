# JCPaid Agents — AI Staffing Agency Core Team
**Version:** 1.0 | 2026-04-22
**Business:** Joseph Vanleur — AI Employee Agency

---

## The Business Model

JCPaid sells AI employee agencies to ANY vertical — restaurants, plumbers, dentists, chiropractors, salons, etc.

For each vertical:
1. We deploy a JackConnect-style install with vertical-specific agents
2. Client records Watch Once skills → automation kicks in
3. They pay $99-499/month depending on tier
4. Dashboard shows time saved = selling point

**Copy-and-train model:**
The hard part (BitNet + Paperclip + Solomon OS + Watch Once + Dashboard) is DONE. New vertical = swap the 7 agents + train on vertical-specific workflows.

---

## The 7 Core Agents
Every JCPaid installation runs these agents.

### 1. Lead Scout Agent
**Purpose:** Find businesses ready for AI employees
**Model:** qwen3:1.7b (BitNet optimized)
**Trigger:** Every morning + on-demand via Telegram
**What it does:**
- Searches Google Maps for local businesses (restaurants, plumbers, dentists, salons)
- Checks: no online booking, old website, < 4★ reviews, no automation visible
- Scores each lead 1-10 on "AI readiness"
- Outputs: ranked list of cold leads with specific automation gaps identified
**Example output:**
"🍽️ Luigi's Pizzeria (downtown) — no online ordering, 3 outdated photos, booked by phone only. Score: 9/10. Quick win: online ordering + reminder texts."
**Prompt hook:**
`/scout restaurants near Chicago` or `/scout plumbers 60601`

---

### 2. Client Acquisition Agent
**Purpose:** Draft outreach that sounds human, book demos
**Model:** qwen3:1.7b (BitNet optimized)
**Trigger:** After Lead Scout delivers leads
**What it does:**
- Generates personalized emails/DMs for each lead
- Personalization: uses business name, recent reviews, specific gap found
- Tracks: message sent → opened → replied → demo booked
- A/B tests subject lines and copy
**Safety:** All messages must be approved by Joseph before sending (human-in-loop)
**Prompt hook:**
`/draft outreach for Luigos Pizza` or `/email Luigi's`

---

### 3. Agent Builder Agent
**Purpose:** Configure new client's vertical agents from templates
**Model:** qwen3:14b (complex reasoning)
**Trigger:** Manually after client signs up
**What it does:**
- Takes client's business type + workflow description
- Selects from 7 agent templates + customizes for their industry
- Creates their Watch Once skills from recorded workflows
- Configures Telegram bot with their account
- Test-runs all agents, reports any failures
**Example:**
"New client: Marco's Taco Truck. Industry: restaurant. Workflow: morning prep → order check → social post. Building agents..."
- 🍽️ Order Agent (online orders, DoorDash updates)
- 📅 Prep Agent (morning checklist, ingredient low alerts)
- 📣 Social Agent (daily specials to Instagram/Facebook)
- 💰 Billing Agent (Stripe payout tracking, expense logging)
**Prompt hook:**
`/build agents for Marco's Tacos` or `/onboard marco@tacos.com`

---

### 4. Onboarding Agent
**Purpose:** Make new clients fall in love with their AI team on day 1
**Model:** qwen3:1.7b (conversational)
**Trigger:** Automatically when new client account created
**What it does:**
- Sends welcome Telegram message: "Your AI team is ready. Here's what each agent does..."
- Walks through Clicky setup (Watch Once recording)
- Records first workflow with client (screen share session)
- Creates first automated task from their real work
- Sends end-of-day summary: "Here's what we set up today. Here's what you'll save this week."
**Client must:** Connect Gmail, Google Calendar, Stripe (guiding them step by step)
**Prompt hook:**
`/start onboarding` or `/onboard`

---

### 5. Billing Agent
**Purpose:** Keep the money flowing, prevent churn
**Model:** qwen3:1.7b
**Trigger:** 1st of month + weekly review
**What it does:**
- Tracks active clients + subscription tier
- Generates invoices, sends payment links via Stripe
- Alerts Joseph: "Maria's restaurant — renewal in 7 days, usage at 92%. Suggest upgrade conversation."
- Flags: missed payments, downgrade requests, cancellation signals
- Reports: Monthly MRR, churn rate, upgrade rate
**Prompt hook:**
`/billing status` or `/invoice Maria's`

---

### 6. Content Agent
**Purpose:** Fill the pipeline with inbound leads via social proof
**Model:** qwen3:14b (creative + storytelling)
**Trigger:** 3x per week (Mon/Wed/Fri morning)
**What it does:**
- Pulls real stats from JackConnect dashboard (hours saved, tasks automated)
- Generates LinkedIn/X posts: case studies, time metrics, vertical launches
- Attaches: screenshots of dashboard, anonymized client wins
- Tracks: impressions, clicks, leads generated per post
- Suggests: "This post got 12 leads — want to do more like it?"
**Example post:**
"Jack, a real estate agent in Chicago, spent 3 hours every week sending follow-up emails. His AI employee now does it in 4 minutes, automatically. That's 11 hours a month back for the things that actually grow his business. This is what JCPaid does — give local businesses their time back."
**Prompt hook:**
`/post this week` or `/create content`

---

### 7. Pipeline Manager Agent
**Purpose:** Never let a hot lead go cold
**Model:** qwen3:1.7b
**Trigger:** Every morning (7 AM CT)
**What it does:**
- Morning briefing to Joseph via Telegram:
  • Hot leads needing follow-up today
  • Demos scheduled
  • Pending contracts/invoices
  • Content that's performing
  • Any billing issues
- Sends reminders throughout the day
- After every demo: "Follow up with [name] in 2 days. Here's what they said they needed."
**Prompt hook:**
`/pipeline` or `/brief me`

---

## Watch Once Skills (JCPaid Specific)
These are workflows Joseph records once → runs forever.

### Lead Scout Skill
Recorded: Joseph doing a Google Maps search for a specific vertical
Learns: Search parameters, scoring criteria, lead format
Runs: Every morning, outputs fresh lead list

### Outreach Skill
Recorded: Joseph drafting a personalized email in Gmail
Learns: Tone, personalization format, subject line patterns
Runs: On new lead, generates draft email for approval

### Onboarding Skill
Recorded: Joseph walking a new client through Telegram setup
Learns: Step-by-step guide, common questions, responses
Runs: Automatically for every new client

### Content Skill
Recorded: Joseph creating a LinkedIn post in Buffer/Hootsuite
Learns: Format, timing, hashtag strategy, CTA style
Runs: 3x/week on schedule

---

## Tier Structure

| Tier | Price | Agents | Who it's for |
|------|-------|--------|--------------|
| **Starter** | $99/mo | 3 agents | Solopreneurs, single location |
| **Professional** | $199/mo | 7 agents | Local businesses, 1-5 employees |
| **Agency** | $499/mo | Unlimited + white-label | Multi-location, franchise, MSP |

---

## Vertical Templates (Ready to Deploy)

### Restaurant Template
- Order Agent (online ordering integration)
- Prep Agent (morning checklist)
- Social Agent (menu updates, specials)
- Review Agent (Google review responses)
- Billing Agent (Stripe + expense tracking)

### Plumber Template
- Lead Qualifier Agent (phone/email lead scoring)
- Scheduling Agent (calendar booking, route optimization)
- Invoice Agent (job costing, payment follow-up)
- Social Agent (before/after photos, local SEO posts)
- Reactivation Agent (annual drain cleaning reminders)

### Dentist Template
- Recall Agent (6-month appointment reminders)
- Insurance Agent (benefits verification, claim follow-up)
- Review Agent (post-visit review requests)
- Reactivation Agent (lapsed patient win-back)
- Social Agent (oral health tips, smile of the week)

### Salon Template
- Booking Agent (online scheduling, reminder texts)
- Product Agent (retail recommendations post-service)
- Reactivation Agent (no-show in 8 weeks)
- Social Agent (styles, transformations)
- Billing Agent (package expiration tracking)

---

*JCPaid — AI Employees for Local Businesses*
*Built on Solomon OS + Paperclip + BitNet*