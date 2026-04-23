# PetPal — Dog Co-Parent / All-Pets Care App
**Version:** 1.0 | 2026-04-23
**Status:** LIVE — Remio aApp Challenge Submission
**URL:** https://josephv.zo.space/petpal

## Concept & Vision

**Tagline:** "Pet care, finally shared."

PetPal is the app that turns "who walked the dog?" into a answered question. One place for every pet in the household — logged by anyone, visible to everyone. For families with multiple pets and multiple caretakers, PetPal ends the "I thought you fed him" conversation forever.

**The feeling:** Like a shared whiteboard on the fridge, but smarter. Anyone in the family can log an action in 2 seconds. Everyone knows the pet's status instantly.

---

## Features

### Multi-Pet Households
- Add unlimited pets (dog, cat, bird, fish, rabbit, hamster, horse, reptile)
- Pet selector strip — switch between pets in one tap
- Each pet has its own photo, type, breed, age, weight, color theme
- Pet type determines which quick-log buttons appear

### Natural Language Quick Log
Just type what happened:
- "I walked buddy" → logs walk with timestamp
- "fed luna" → logs feeding
- "gave max his medicine" → logs medication
- "bath time for ruby" → logs bath
Fallback: logs free-text entry if no keyword matches

### One-Tap Quick Log Buttons
Smart buttons per pet type:
- Dog: Walk, Feed, Med, Potty, Bath, Groom, Vet
- Cat: Feed, Litter box, Med, Brush, Nail trim
- Fish: Feed, Water change, Temp check
- Rabbit: Feed, Litter box, Groom, Fresh hay
- And more for each type

### Care Log
- Every entry: who did it, what they did, when
- Color-coded by action type
- Full household history

### Co-Parent Team
- Add family members, dog walkers, pet sitters
- Active / limited permissions
- Everyone sees the same log

### Health Tracking
- Weight chart over time
- Medication schedule with next dose
- Vaccine records

### Schedule
- Weekly view of upcoming tasks
- Vet appointments, medication reminders

### Lost Pet Mode
- One-tap "LOST?" button
- Full-screen red alert overlay
- Location share button

---

## Technical

- Built on: React + Tailwind CSS, zo.space page route
- No backend — localStorage for persistence
- Pet photos: base64 encoded, stored locally
- Fully mobile-first

---

## Competition

| App | What it does | Our advantage |
|-----|-------------|---------------|
| Tissue | Generic pet journal | We do more pet types + co-parenting |
| DogLog | Walking tracker | We have natural language + multi-pet |
| Paw卡 | Pet care | We integrate family co-parenting |

---

*PetPal — Built on Solomon OS for the Remio aApp Challenge*
*2026-04-23*