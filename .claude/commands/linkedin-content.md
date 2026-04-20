# /linkedin-content — First Rain Weekly LinkedIn Content Generator
# Consolidated from /linkedin-post as of 20 Apr 2026
# Load when: generating weekly LinkedIn posts for Niloy's personal profile.

Generates 5 LinkedIn posts for the current week. Posts are voice-accurate, sector-targeted, and ready to paste into LinkedIn.

---

## STEP 0 — Story Seed Input

Ask Niloy:

> "Do you have a Story Seed this week? (A specific observation, client moment, show floor detail, or field experience — paste it here or type none.) If provided, anchor at least one post this week to it."

If a seed is provided, anchor at least one post directly to it — use the specific detail, do not generalise it away.
If 'none', generate from live project context in _context/active-projects.md and current industry moment.

---

## STEP 1 — Load Context

Read:
- `_context/active-projects.md` — for live project context and show calendar
- `_context/brand-voice.md` — for voice rules (non-negotiable)

Do NOT load any other files unless Niloy references a specific client or show.

---

## STEP 2 — Voice Rules (non-negotiable)

Source: `_context/brand-voice.md`

- Niloy's voice: direct, founder-perspective, personal observation, never promotional
- Show-specific: name the show, the challenge, the learning — be concrete
- Short sentences. One idea per paragraph.
- 150–250 words per post (Field Dispatch: 150–220 words — hard cap)
- Max 3 hashtags per post — no hashtag spam, no generic tags
- End with a question or a single clear point — no call to action fluff
- Never: fluffy openers, "excited to share", bullet-point tip threads, listicles
- Never: "In today's fast-paced world", "game-changing", "leverage", "synergy"
- Always: first person, grounded in a specific observation or project moment

---

## STEP 3 — ICP Targeting

Posts are written for:
- Marketing CXOs, Head of Marketing, VP Marketing, Brand Managers, Exhibition Managers
- Companies ₹100 Crore+ annual revenue, exhibiting 2+ shows per year
- Core fear: Exhibition failure = brand damage + personal career risk

First Rain's 13 active target sectors — assign one sector to every post:

1. Pharma/Life Sciences
2. Food & Beverage
3. Chemicals/Specialty Chemicals
4. Energy/Renewables
5. Manufacturing/Engineering
6. Electrical/Electronics
7. Automotive
8. Construction/Infrastructure
9. Textiles
10. Media/AV/Entertainment
11. Fintech
12. Gems & Jewellery
13. Agri/Food Processing

Each post must be tagged at the bottom:
`Target sector: [Sector Name]`

Rotate sectors across the week. Do not repeat a sector twice in the same week unless explicitly requested.

---

## STEP 4 — Weekly Post Formats

| Day       | Format          | Description |
|-----------|-----------------|-------------|
| Monday    | Insight Post    | Industry observation or founder POV. Problem-first. No tips. Leaves the reader with one sharp thought. |
| Tuesday   | Client Lens     | A project, a challenge, a result. Show-specific. Concrete detail. No client name without permission — describe the brief, the sector, the outcome. |
| Wednesday | Behind the Build | Process detail. What most clients never see. Fabrication, logistics, site reality. Builds authority through specificity. |
| Thursday  | International   | Global show context — European or international platform. Positions First Rain beyond India. Leads with the specific challenge of cross-border work. |
| Friday    | Field Dispatch  | A raw, unfiltered dispatch from the exhibition floor, client site, or travel moment. First-person, present tense, cinematic detail. No tips, no listicles. Just what you saw, smelled, heard, or felt — and the one thought it triggered. 150–220 words max. Hard cap. |

---

## STEP 5 — Generate Posts

Generate all 5 posts for the week. For each post include:

```
---
[DAY], [DATE] — [FORMAT TYPE]
---

[Post copy — ready to paste into LinkedIn]

[Hashtags — max 3]

Target sector: [Sector Name]
```

Do not add any framing text around the posts. Deliver them clean, copy-paste ready.

---

## STEP 6 — Save Output

Save to: `_outputs/linkedin-content/week-[DD-Mon-YYYY].md`

Use this file header:

```
# LinkedIn Content — Week of [DD Month YYYY]
# Generated: [today's date]
# Voice: Niloy Debnath, Director, First Rain Exhibits India
```

Confirm the file path after saving.
