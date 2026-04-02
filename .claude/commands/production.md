# /production — First Rain Production Check

## APPROACH — 2 rounds. Always live. No cache.

**Round 1:** 7 parallel searches of Tasks DB → collect all task URLs
**Round 2:** Batch fetch all URLs in parallel → Status + Project per task
**Output:** Grouped by project, DONE / PENDING split, flags applied.

---

## KNOWN PROJECT MAP — hardcoded, no re-fetch needed

| Project URL contains | Name | Show | Dates | Days | Exec | Fabricator |
|---|---|---|---|---|---|---|
| `334772f4...c381` | Bechem BME'26 | BME Delhi | 8–9 Apr 2026 | 7 | Chinmay | ⚠️ BLANK |
| `335772f4...5892` | Labguard Anacon'26 | Analytica Lab India | 22–24 Apr 2026 | 21 | Smita | ⚠️ BLANK |
| `7ea772f4...82ff` | Mosil IDMC'26 | IDMC Lucknow | 23–24 Apr 2026 | 22 | Dhruv | Nandu |
| `325772f4...8073` | Messung SHE'26 | Smart Home Expo | 28–30 Apr 2026 | 27 | Shilpa | Rahul Exporacle |
| `334772f4...c984` | Amaara Vitafoods | Vitafoods Europe | 5–7 May 2026 | 34 | Shilpa | Ashok Saltwater |

**Tasks DB:** `collection://fe5772f4-6bf1-825a-95f1-07c0e17ebf31`

---

## ROUND 1 — 7 Parallel Searches

Search `collection://fe5772f4-6bf1-825a-95f1-07c0e17ebf31` with ALL 7 queries simultaneously.
Use `page_size=25, max_highlight_length=0` on every call.

| # | Query |
|---|---|
| 1 | `proforma invoice advance customer received` |
| 2 | `costing drawing technical drawing submission organizer` |
| 3 | `fabricator finalisation advance fabricator security deposit` |
| 4 | `internal execution meeting design approval mockup` |
| 5 | `onsite schedule crew booking travel expense approval` |
| 6 | `installation supervision possession handover pics` |
| 7 | `dismantling final invoice payment customer fabricator` |

Collect all **unique** task URLs across all 7 results. Deduplicate by URL.

---

## ROUND 2 — Batch Fetch All Tasks (single parallel burst)

Fetch every unique task URL from Round 1 **in parallel** (one message, many tool calls).
From each page, extract:
- `Task Name` — strip number prefix (e.g. `"1-"`, `"3- "`, `"8 - "`) and project suffix (e.g. `" (1)"`, `" (2)"`) for display
- `Status` — one of: Done / In progress / Not started / On Hold / To Review
- `Project` — array of URLs → match against PROJECT MAP above using URL snippet

---

## STEP 3 — Group & Sort

- Group tasks by project
- Within each project, sort by task number (numeric prefix)
- Split into **DONE** (Status = Done) and **PENDING** (everything else)
- Output projects ordered by show date (Bechem first, Amaara last)

---

## STEP 4 — Critical Path Rules

Apply **per project** based on days to show:

| Days to show | Tasks that must be Done | Severity |
|---|---|---|
| < 7 days | ALL tasks 1–20 | 🔴 URGENT |
| 7–14 days | Tasks 1–19 | 🔴 flag |
| 15–30 days | Tasks 1–12 | 🟠 flag |
| > 30 days | Tasks 1–4 | ⚠️ warn if Not Started |

Flag **any** On Hold task regardless of days.
Flag **missing fabricator** regardless of days.

---

## OUTPUT FORMAT (per project)

```
[PROJECT NAME]
Expo: DD Mon → DD Mon | Fabricator: [name or ⚠️ BLANK]

DONE: ✅
- Task name
- Task name

PENDING:
- 🔵 Task name  ← In Progress
- ⬜ Task name  ← Not Started
- 🟠 Task name  ← On Hold

⚠️ FLAGS
- [Task name] — not Done, [N] days to show (critical path breach)
- Fabricator not set — assign before fabrication starts
```

---

## SUMMARY FOOTER

```
PRODUCTION SUMMARY | [Today's Date]
Active: 5 | Closest: [Project] in [N] days | Open flags: [N]
```

---

## STATUS LEGEND
✅ Done · 🔵 In Progress · ⬜ Not Started · 🟠 On Hold · 🔁 To Review

---

## UPDATING TASKS

- **"mark [project] task [name] done"** → use `notion-update-page` on that task's URL, set `Status = Done`
- **"refresh production"** → re-run from Round 1 (always live, no stale data)
- Task URLs are discovered fresh each run — nothing to maintain manually
