---
name: spatial-concept
version: "1.0"
description: >
  Generate 3 spatial design concepts for a stand brief. Run when spatial
  concept, 3 concepts, design options, stand concepts, creative directions,
  layout options, or concept exploration is mentioned. Outputs three
  distinct directions with rationale, must-haves, risks, and rough CP band.
  Always runs AFTER /stand-design-brief has captured the brief.
---

# Spatial Concept — First Rain

## Pre-check — refuse if brief is missing
Before generating any concept, confirm the brief exists. Required inputs:
- Client name + show name + date + venue
- Stall size (sqm) + type (island / 3-side / 2-side / inline)
- Budget range (SP)
- Key message / theme
- Must-haves (demo area, meeting room, storage, AV)

If any of the above is missing → STOP. Reply: "I need the brief first. Run /stand-design-brief."

## Reference files to load
- `_context/financial-rules.md` — margin floor check on budget
- `_context/brand-voice.md` — voice of rationale copy
- `_context/clients.md` — if existing client, load their pricing rules
- `_context/competitive-landscape.md` — avoid concept patterns used by competitors

## Margin pre-flight
Before writing concepts, run the implicit margin check:
- Calculate CP ceiling at 33% India / 38% International
- If budget is tight (CP ceiling < ₹X/sqm for stall type), flag: "Budget is tight — concepts must respect CP ceiling of ₹[amount]"
- Never propose a concept that can only be built below margin floor

## Output format — always exactly this

```
SPATIAL CONCEPTS — [Client] · [Show] · [Size] · [Date]

Brief summary: [one sentence]
Budget: SP ₹[X]L | CP ceiling at 33%: ₹[Y]L | CP/sqm cap: ₹[Z]
Floor: 33% India / 38% International

================================================================
CONCEPT 1 — [Name, 2-4 words]
Direction: [one sentence — the big idea]
Spatial moves:
  - [Primary move — hero element]
  - [Secondary move — flow/zoning]
  - [Tertiary move — material/finish]
Visitor journey: [entry → hook → engage → meeting → exit, in 3-4 steps]
Must-have checklist: [demo ✅/❌] [meeting room ✅/❌] [storage ✅/❌] [AV ✅/❌]
Rough CP band: ₹[low]–[high]L
Margin at mid-range: [X%]  [✅ PASS / 🔴 FAIL]
Why this works: [2 sentences — tied to client fear or show context]
Risk: [one sentence — what could go wrong in build]

================================================================
CONCEPT 2 — [Name]
[same structure]

================================================================
CONCEPT 3 — [Name]
[same structure]

================================================================
Recommendation: [Concept N, one sentence why]
Mangesh review required before client sees any concept.
```

## Rules for the 3 concepts — must be genuinely different
- **Concept 1** — the safe, proven direction (closest to what they asked for)
- **Concept 2** — the bold stretch (bigger hero moment, higher impact)
- **Concept 3** — the contrarian play (challenges the brief assumption — different flow, different anchor)

Never produce three variations of the same idea. If you cannot make them genuinely distinct, say so and ask Niloy to reframe the brief.

## After output
- Save to `_outputs/concepts-[client]-[show]-[YYYY-MM-DD].md`
- Flag: "Mangesh review required before anything leaves _outputs/"
- If any concept flagged 🔴 FAIL margin → drop it and propose a 4th, or tell Niloy the brief needs budget reset
