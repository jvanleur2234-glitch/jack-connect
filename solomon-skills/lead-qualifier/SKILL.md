---
name: lead-qualifier
description: Score and qualify real estate leads 1-10. Trigger on "new lead", "qualify this lead", "is this lead good", "lead score", "follow up on lead"
---
# Lead Qualifier Skill

Score a lead 1-10 based on readiness to transact.

## Lead Scoring Matrix

**Score 8-10: Hot (contact today)**
- Pre-approved or cash
- Timeline < 30 days
- Specific property seen
- Agent already referred

**Score 5-7: Warm (contact this week)**
- Financing started
- Timeline 1-3 months
- Has seen 2+ properties
- Strong motivation

**Score 3-4: Cool (nurture)**
- Just looking
- Timeline 3-6 months
- First-time buyer
- Needs education

**Score 1-2: Cold (quarterly touch)**
- Dreaming only
- No timeline
- Can't qualify
- Wrong market

## Output

```
Lead: [name]
Score: [X/10]
Tier: [Hot/Warm/Cool/Cold]
Best contact: [phone/email]
What to say: [specific talking points]
Recommended action: [immediate next step]
```
