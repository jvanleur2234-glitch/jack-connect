---
name: real-estate-cma
description: Generate a Comparative Market Analysis report for real estate. Trigger on "CMA", "market analysis", "comps report", "property comparison", "what's my home worth"
---
# Real Estate CMA Skill

Generate a professional Comparative Market Analysis report for a property.

## Inputs (from user or CRM)

- Property address
- Property specs (beds, baths, sqft, lot size, year built)
- Client name and contact
- Client motivation (buying, selling, refinancing)
- Timeframe

## How to Run

1. Research the property on MLS / public records
2. Find 3-5 comparable properties (sold in last 90 days, same neighborhood)
3. Analyze pricing trends in the area
4. Generate the CMA report

## CMA Report Structure

```
# Comparative Market Analysis
**Property:** [address]
**Prepared for:** [client name]
**Date:** [today]
**Purpose:** [buying/selling/refinancing]

## Subject Property
[Address, beds, baths, sqft, lot, year built, MLS#]

## Comparable Sales
| Address | Beds | Baths | SqFt | Lot | Sold $ | DOM | $/SqFt |
|---------|------|-------|------|-----|--------|-----|--------|
| ...     | ...  | ...   | ...  | ... | ...    | ... | ...    |

## Market Analysis
- Average DOM: X days
- Avg sold $/sqft: $X
- Price trend: [up/down/stable] X% over 90 days
- Inventory: X months of supply

## Subject Property Valuation
- Low: $[based on smallest comps]
- Mid: $[based on adjusted comps]
- High: $[based on strongest comps]

## Recommendation
[Specific advice for client's situation]

## Next Steps
- [ ] Step 1
- [ ] Step 2
```

## Output Format

Return the CMA as a formatted markdown report. Then ask:
"Ready to send this to [client name]? I can email it, text it, or save it to your CRM."

## Auto-Trigger

If Jack mentions "run CMA" or "market analysis for [address]" — run this skill automatically.
