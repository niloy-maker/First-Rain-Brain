---
name: weekly-report
version: "1.0"
description: >
  Compile the 5 department weekly reports from Google Drive into a single
  Monday L10 briefing document. Run when weekly report, weekly compile,
  Sunday compile, department reports, or "pull Friday reports" is mentioned.
  Also runs automatically via /schedule on Sunday 20:00 local.
---

# Weekly Report Compiler — First Rain

## Purpose
On Sunday evening, read each department's Friday weekly report from Google Drive
and compile a single briefing document that feeds directly into Monday's L10
meeting via `/monday`. This replaces Niloy manually opening 5 Drive folders.

## Reference files
- `_context/active-projects.md` — Q1 Rocks, Scorecard targets, active quotes
- `_context/financial-rules.md` — current cash, receivables, burn rate
- `_context/team-map.md` — who owns which department
- `_context/session-log.md` — last 3 entries (for continuity)

## Google Drive layout expected
```
FirstRain-Weekly-Reports/
├── Growth/          ← Pankaj + Dhruv
├── Client-Delivery/ ← Chinmay + Shilpa
├── Design/          ← Mangesh + Komal
├── Finance/         ← Sonal
├── People/          ← Niloy
└── Archive/         ← older than 4 weeks
```

Each department submits one file per week, filename pattern:
`W[week-number]-[YYYY]-[dept]-[author].md` (e.g. `W15-2026-Growth-Pankaj.md`)

## Step 1 — Parallel fetch (if Drive MCP available)
Use any available Google Drive MCP (`google_drive_search` / `google_drive_fetch`
or `gws` if installed). Spawn 5 parallel subagents — one per department — to
read this week's file. Cuts compile time from ~5 min to ~90 seconds.

Subagent 1 → Growth folder
Subagent 2 → Client-Delivery folder
Subagent 3 → Design folder
Subagent 4 → Finance folder
Subagent 5 → People folder

## Step 2 — Fallback if no Drive access
If no Drive MCP is available OR a department file is missing:
- Flag the specific missing department: "⚠️ No Growth report from Pankaj this week"
- Ask Niloy: "Paste the 5 reports inline and I'll compile them"
- Do NOT guess, do NOT invent numbers, do NOT leave the row blank

## Step 3 — Compile into this exact format

```
FIRST RAIN WEEKLY REPORT — W[N] · [date range]
Auto-compiled [day] [time] by /weekly-report

## HEADLINE
[One sentence — the single most important thing from the week across all departments]

## SCORECARD (cross-reference active-projects.md targets)
| Metric                    | Target   | This Week | Status |
|---------------------------|----------|-----------|--------|
| New qualified leads       | 5+/week  | [X]       | ✅/🔴  |
| LinkedIn acceptance rate  | 55%+     | [X%]      | ✅/🔴  |
| Email reply rate          | 8%+      | [X%]      | ✅/🔴  |
| Active quotes             | 3+       | [X]       | ✅/🔴  |
| Receivables collected     | ₹5L+     | ₹[X]L     | ✅/🔴  |
| CM on active quotes       | 33%+     | [X%]      | ✅/🔴  |
| Secure pipeline %         | <50%     | [X%]      | ✅/🔴  |

## DEPARTMENT HEADLINES
### 01 Growth (Pankaj + Dhruv)
- Headline: [1 sentence]
- Wins: [bullets from their report]
- Blockers: [bullets]
- Ask from Niloy: [if any]

### 02 Client Delivery (Chinmay + Shilpa)
[same format]

### 03 Design (Mangesh + Komal)
[same format]

### 04 Finance (Sonal)
- Cash: ₹[X]L operating / ₹[X]L treasury
- Receivables collected this week: ₹[X]L
- Receivables outstanding top 5: [list]
- Flags: [any burn rate / margin / concentration alerts]

### 05 People (Niloy)
[same format]

## Q1 ROCKS — STATUS CHANGE THIS WEEK
| # | Rock | Last Week | This Week |
|---|------|-----------|-----------|
| 1 | 3 new enterprise accounts | [status] | [status] |
| 2 | Secure below 40% | [status] | [status] |
| 3 | Sales Hunter hired | [status] | [status] |
| 4 | CPhI China 10 enquiries | [status] | [status] |
| 5 | 6 skill files live | [status] | [status] |
| 6 | Secure Utility Week PO | [status] | [status] |

## ALERTS — MUST RAISE IN MONDAY L10
- [Any margin breach]
- [Any Secure concentration breach — currently 52.5%]
- [Any receivable overdue >30 days]
- [Any single-point-of-failure surfacing]
- [Any Elliott Ebara "verbal revenue" creeping in]

## TOP 3 ISSUES FOR MONDAY IDS
[Auto-surface from the blockers + alerts. Maximum 3.]
1. [Issue — from which department]
2. [Issue]
3. [Issue]

## MISSING REPORTS
[Any department that did not submit this week — name them]

---
Compiled from: [list of Drive file names]
Ready for Monday L10 briefing via /monday
```

## Step 4 — Save outputs
- Primary: `06-Strategy/weekly-reports/W[N]-2026.md`
- Mirror: `_outputs/weekly-[YYYY-MM-DD].md`

## Step 5 — Hand off to /monday
After saving, echo this line:
> "Weekly report W[N] ready. Run /monday tomorrow to convert into L10 briefing."

## Rules
- NEVER invent numbers. If a department didn't submit, flag the gap — don't hallucinate.
- NEVER fill in Scorecard from memory. Only from this week's submissions.
- ALWAYS cross-check Finance numbers against `_context/financial-rules.md` — if they drift, flag for Sonal.
- ALWAYS include the Alerts section, even if empty. "No alerts this week" is a valid entry.
- Keep the Top 3 Issues section to exactly 3 (or fewer if the week was quiet).

## Schedule hookup (for when /schedule is set up)
```
/schedule weekly sunday 20:00
Run /weekly-report
```
The skill runs in Anthropic's cloud — Mac does not need to be on.
