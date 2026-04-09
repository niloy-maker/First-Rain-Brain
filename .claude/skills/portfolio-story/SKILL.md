---
name: portfolio-story
version: "1.0"
description: >
  Convert a completed project into a reusable case study. Run when portfolio,
  case study, project story, finished project, post-show writeup, completed
  build, or "write up the [client] stand" is mentioned. Outputs a Brief →
  Design → Build → Outcome format that fits email, WhatsApp, LinkedIn, and
  landing page use — from one source file.
---

# Portfolio Story — First Rain

## Reference files
- `_context/brand-voice.md` — Niloy's voice, no filler, data first
- `_context/clients.md` — confirm NDAs or client restrictions before using names
- `_context/active-projects.md` — confirm project is actually completed (not in-build)

## Pre-check — refuse if project isn't done
Do NOT write a portfolio story for a project that is still in build, or where
the show hasn't happened yet. Reply: "This project is still active. Run
/portfolio-story after show closes."

## Inputs to collect (ask in order)
1. Client name + show + date + location (confirm against active-projects.md)
2. Stall size + type (island / 3-side / inline)
3. SP (for internal version only — never in public copy)
4. The brief in one sentence — what did they actually need?
5. The design challenge — what was hard about this?
6. The key spatial move — the thing that made the stand work
7. Outcome — visitor count / meetings booked / leads generated / client feedback
8. Images available? (how many, hero shot, detail shots, visitor shots)

If outcome data is missing → flag "Need outcome numbers before publishing" but still draft.

## Output format — always generate 4 versions from one source

### Version 1: MASTER (internal, full detail)
```
PORTFOLIO STORY — [Client] · [Show] · [Date]

THE BRIEF
[2 sentences — what they needed, why it mattered]

THE CHALLENGE
[2 sentences — the specific design problem]

THE DESIGN
[3 sentences — the key spatial move, materials, visitor journey]

THE BUILD
[2 sentences — any interesting production detail, fabricator, timeline]

THE OUTCOME
[3 bullet points — measurable results]
- [Metric 1]
- [Metric 2]
- [Metric 3]

Internal: SP ₹[X]L | CM [X%] | Exec: [Name]
```

### Version 2: LINKEDIN POST (public, 150-250 words)
Load `_context/brand-voice.md` rules. No filler. Personal observation.
Name the show. Name the challenge. End with one clear point or question.
Max 3 hashtags. Never promotional.

### Version 3: CLIENT EMAIL (warm thank-you, <150 words)
Direct. Client first name. Reference the specific show. Share the result.
One sentence asking about the next show. Sign off.

### Version 4: WHATSAPP / 1-LINER (<80 words)
The hook only. Use for DM follow-ups, cold-lead warming, or case study mentions
in outbound email templates.

## Rules
- Never name a client without confirming they permit it (check `clients.md` — default ASSUME no)
- Never use SP/CP/margin in any public version
- Never claim an outcome you didn't verify with the client
- Always include 1 specific, credible metric (not "client was happy")
- If no metric available → write the MASTER version only, mark LinkedIn/Email/WhatsApp as "DRAFT — needs outcome data"

## Save to
`_outputs/portfolio-[client]-[show]-[YYYY-MM-DD].md`

Routing: Mangesh reviews for design accuracy. Niloy approves public versions before publish.
