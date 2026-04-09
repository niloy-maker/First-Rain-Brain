# /production — First Rain Production Check

## APPROACH — 1 fetch. Always live. No cache.

Fetch the ⚡ FR Production Tracker FY27 collection in a single call.
Parse all 31 milestone rows. Output grouped status per project.

**Collection:** `collection://965e6417-5103-4dd0-9b9f-b082bfe0a75f`
**Board URL:** https://www.notion.so/ac84c676ad7249d2a79732d842f71d62

---

## KNOWN PROJECT MAP — hardcoded, no re-fetch needed

| Column Name | Project | Show | Dates | Days to Show | Exec | Fabricator |
|---|---|---|---|---|---|---|
| Bechem BME26 | Bechem BME'26 | BME Delhi | 8–9 Apr 2026 | 6 | Chinmay | ⚠️ BLANK |
| Labguard Anacon26 | Labguard Anacon'26 | Analytica Lab India | 22–24 Apr 2026 | 20 | Smita | ⚠️ BLANK |
| Mosil IDMC26 | Mosil IDMC'26 | IDMC Lucknow | 23–24 Apr 2026 | 21 | Dhruv | Nandu |
| Messung SHE26 | Messung SHE'26 | Smart Home Expo | 28–30 Apr 2026 | 26 | Shilpa | Rahul Exporacle |
| Amaara Vitafoods26 | Amaara Vitafoods | Vitafoods Europe | 5–7 May 2026 | 33 | Shilpa | Ashok Saltwater |

---

## STEP 1 — Single Fetch

Call `notion-fetch` on the board URL:
```
https://www.notion.so/ac84c676ad7249d2a79732d842f71d62
```

Or search collection `collection://965e6417-5103-4dd0-9b9f-b082bfe0a75f` with an empty/broad query, `page_size=50`.

Each row returns:
- `Milestone` — task name (e.g. "T04 Fabricator Finalisation")
- `Bechem BME26` — `__YES__` or `__NO__`
- `Labguard Anacon26` — `__YES__` or `__NO__`
- `Mosil IDMC26` — `__YES__` or `__NO__`
- `Messung SHE26` — `__YES__` or `__NO__`
- `Amaara Vitafoods26` — `__YES__` or `__NO__`

---

## STEP 2 — Parse & Transpose

For each project column, collect:
- **DONE** tasks: rows where that column = `__YES__`
- **PENDING** tasks: rows where that column = `__NO__`

Sort by task number (numeric prefix T01, T02 … T31).

---

## STEP 3 — Critical Path Rules

Apply **per project** based on days to show:

| Days to show | Tasks that must be ✅ | Severity |
|---|---|---|
| < 7 days | ALL tasks T01–T20 | 🔴 URGENT |
| 7–14 days | T01–T19 | 🔴 flag |
| 15–30 days | T01–T12 | 🟠 flag |
| > 30 days | T01–T04 | ⚠️ warn if pending |

Flag **missing fabricator** regardless of days.

---

## OUTPUT FORMAT (per project)

```
[PROJECT NAME]
Show: DD Mon → DD Mon | Exec: [name] | Fabricator: [name or ⚠️ BLANK]

✅ DONE (N):
T01 Proforma Invoice Sent
T04 Fabricator Finalisation

⬜ PENDING (N):
T02 Advance Received – Client
T03 Costing & Drawing
...

⚠️ FLAGS
- T03 Costing & Drawing — pending, 6 days to show (critical path breach)
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
✅ Done (checked) · ⬜ Pending (unchecked)

---

## UPDATING TASKS

- **"mark [project] [task] done"** → use `notion-update-page` on the T-row's page URL, set the project's checkbox = `__YES__`
- **"refresh production"** → re-fetch the board URL (always live, no stale data)
- To find a row's page URL: it was returned in the original create-pages call, or fetch the collection and get the page ID from results

## MILESTONE ROW PAGE IDs (for direct updates)

| Milestone | Page URL |
|---|---|
| T01 Proforma Invoice Sent | https://www.notion.so/336772f46bf181c4aeacf002b54ba580 |
| T02 Advance Received – Client | https://www.notion.so/336772f46bf181f699ccd0b0bd4b3831 |
| T03 Costing & Drawing | https://www.notion.so/336772f46bf181e4a7fcd57030b62fc0 |
| T04 Fabricator Finalisation | https://www.notion.so/336772f46bf181e9981ed05637ea8045 |
| T05 Advance to Fabricator | https://www.notion.so/336772f46bf1812ba493c7a2c7ec41a1 |
| T06 Internal Execution Meeting | https://www.notion.so/336772f46bf18199a85dcdcfef9517a1 |
| T07 Technical Drawing | https://www.notion.so/336772f46bf181dd9a64e1b525791605 |
| T08 Fabricator Meeting | https://www.notion.so/336772f46bf18157a6d9dafaf3870be5 |
| T09 Submission Drawings | https://www.notion.so/336772f46bf181f78e72ccd31c47d032 |
| T10 Design Approval + Permission to Build | https://www.notion.so/336772f46bf1819bb850cd5f59b59122 |
| T11 Organiser Form Submissions | https://www.notion.so/336772f46bf181b28666c386afee49db |
| T12 Security Deposit | https://www.notion.so/336772f46bf1813a9075fdf2c2e73bd7 |
| T13 Material Approval from MAM | https://www.notion.so/336772f46bf181a2bfdbc21c7604c7ac |
| T14 Mock Up | https://www.notion.so/336772f46bf181a4b88dc58d9ffa45db |
| T15 Onsite Schedule from Fabricator | https://www.notion.so/336772f46bf1812295acc0102d15798d |
| T16 Travel Expense Approval | https://www.notion.so/336772f46bf181bd926df6f35ba2f955 |
| T17 Crew Travel Booking | https://www.notion.so/336772f46bf181f0b934de3f22cd7886 |
| T18 Graphics & Logo Checking | https://www.notion.so/336772f46bf181468a1edbd9317b7d0b |
| T19 Graphics & Logo to Fabricator | https://www.notion.so/336772f46bf181a7978ceaece098b5e7 |
| T20 Possession Pics | https://www.notion.so/336772f46bf181f4adb2f35893a2f574 |
| T21 Installation Started | https://www.notion.so/336772f46bf181898363d410a11655e2 |
| T22 Handover Pics | https://www.notion.so/336772f46bf1810ab353e0ce58cc0b4d |
| T23 Dismantling Pics | https://www.notion.so/336772f46bf181d4a9c3d5acdfd93032 |
| T24 Incremental Billing (IA) | https://www.notion.so/336772f46bf181078288d1ca2520173e |
| T25 Customer Feedback Meeting | https://www.notion.so/336772f46bf1815f9910de6e8523c0d5 |
| T26 Thank You Mail | https://www.notion.so/336772f46bf18136bf67e8dbe0bf508c |
| T27 Final Invoice | https://www.notion.so/336772f46bf1817cbf88f79d0e63f91a |
| T28 Final Payment | https://www.notion.so/336772f46bf181a89275ffc9ba164c3b |
| T29 Deposit Return | https://www.notion.so/336772f46bf181e78569c533cb872af9 |
| T30 Fabricator Feedback Meeting | https://www.notion.so/336772f46bf18119afd3ef9f97c2e794 |
| T31 Fabricator Final Meeting | https://www.notion.so/336772f46bf18112b0a9c7aa4c097152 |
