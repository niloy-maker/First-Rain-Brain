---
name: sop-writer
version: "1.0"
description: >
  Convert a productive working session into a reusable SOP (Standard
  Operating Procedure). Run when Niloy says "turn this into an SOP",
  "document this process", "we should systematise this", "this worked —
  save it", "write up how we do X", or when a recurring workflow is
  successfully completed and worth capturing.
---

# SOP Writer — First Rain

## When to run
- After a successful workflow that Niloy wants to repeat (and delegate)
- When a one-off fix should become a permanent process
- When a fragile single-point dependency (Sonal / Mangesh / Santosh) needs to be documented before knowledge walks out the door
- Explicitly NOT for: brainstorms, abandoned ideas, half-finished work

## Reference files
- `_context/team-map.md` — to assign the SOP owner correctly
- `_context/brand-voice.md` — short sentences, no filler
- `_context/active-projects.md` — if SOP is project-specific

## Inputs to collect
1. What happened? (one sentence — the trigger)
2. What worked? (the key steps, in order)
3. Who did what? (people and tools involved)
4. What would have gone wrong? (the failure mode this SOP prevents)
5. Who should own this SOP going forward?
6. How often will it run? (per project / weekly / monthly / one-off with trigger)

## Output format — always exactly this

```
SOP: [Clear imperative title, e.g. "How to chase Amaara receivables"]

Version: 1.0 | Created: [date] | Owner: [Name from team-map.md]
Trigger: [When does this SOP kick in? Be specific.]
Frequency: [Per project / weekly / on-event]

## Why this exists
[2 sentences. The failure mode this prevents. The cost of getting it wrong.]

## Prerequisites
- [What must be true before step 1 runs]
- [Files / access / context needed]
- [Any Niloy approval gates]

## Steps
1. [Verb-first action. One clear thing.]
2. [Next action. No fluff.]
3. [Continue. Each step should be doable in under 10 minutes or broken down further.]
4. [...]

## Definition of done
- [Observable outcome 1]
- [Observable outcome 2]
- [Where the evidence is logged]

## Failure modes to watch for
- [Common mistake 1 → what to do instead]
- [Common mistake 2 → what to do instead]

## Escalation
If [specific condition] → escalate to [Niloy / named person].
Never [specific prohibited action].

## Related skills / files
- Skill: /[related-skill]
- Context: _context/[file].md
```

## Rules
- **Verb-first steps.** "Open Zoho Books" not "You should open Zoho Books."
- **One step = one action.** If a step has "and" in it, split it.
- **Under 10 minutes per step.** Longer → break it down.
- **Name real people** from team-map.md — not "the exec" or "someone"
- **Include the failure mode** — why does this SOP exist? If you can't answer, you don't need an SOP yet.
- **Assign an owner.** No owner = no SOP. Flag to Niloy if owner is unclear.

## Anti-patterns — refuse to write
- SOP for a process that only ran once and may not repeat
- SOP that depends on Shilpa doing field work (she is async only — rule)
- SOP that bypasses the margin gate or Elliott Ebara PO-first rule
- SOP without a named owner

## Save to — route by department, not by person
SOPs live in the department folder that owns the outcome, NOT in 05-People
(which is HR only — hiring, reviews, onboarding).

| If the SOP is about...                              | Save to                    |
|-----------------------------------------------------|----------------------------|
| Cash, quotes, margins, receivables, bank, audit     | `04-Finance/SOPs/`         |
| Project delivery, Notion, handover, Doha, fabricator| `02-Client-Delivery/SOPs/` |
| Design brief, concept review, portfolio capture     | `03-Design/SOPs/`          |
| Outbound, ICP, lookalikes, LinkedIn, lead gen       | `01-Growth/SOPs/`          |
| Hiring, reviews, onboarding, team rituals           | `05-People/SOPs/`          |
| L10, rocks, scorecard, decision logging, strategy   | `06-Strategy/SOPs/`        |

Cross-department? Pick the department that owns the **outcome** (not the most
people involved). If unclear → flag to Niloy, do not guess.

Filename: `SOP-[short-title]-v1.md`
If a previous version exists → save as `v[N+1]` and preserve the old one.

## After creating
- Tell Niloy: "SOP created. Owner: [Name]. Next review: [date — default 90 days]."
- Add one line to `_context/decision-log.md` noting the new SOP and owner
