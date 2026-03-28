# P — Projects | First Rain FY26-27
# Load this when: discussing active shows, production status, live quotes, Notion tasks
# Last updated: [date]

## SECTION 14 — PRODUCTION COMMAND

### Trigger
When Niloy types **"Production"**, execute the full sequence below. No preamble. No commentary until the output is complete.

### Step 1 — Display Closed Won Projects (from CRM memory)

Display FY26-27 Closed Won projects month-by-month, ordered by show date.

| Customer | Stall Size | Exhibition | Show Date | Venue | SP (₹) | Exec |
|---|---|---|---|---|---|---|
| Mosil Lubricants | 9 sqm | IDMC Lucknow | 23–24 Apr 2026 | Lucknow | ₹1,50,000 | Dhruv |
| Messung Systems | 42 sqm | Smart Home Expo | 28–30 Apr 2026 | JWCC Mumbai | ₹6,30,000 | Shilpa |

Source: CRM memory (Closed Won only). Do not include Pipeline or TBC entries.

### Step 2 — Fetch Live Task Status from Notion

For each Closed Won project, fetch current task status live from Notion.

- **Notion workspace:** `https://www.notion.so/firstraingroup/26-27-Project-Manager-First-Rain-35b772f46bf1829f956681ec5c16bc13`
- **Projects DB:** `collection://d62772f4-6bf1-82e3-b83d-077710962b4f`
- **Tasks DB:** `collection://fe5772f4-6bf1-825a-95f1-07c0e17ebf31`

**Method:**
1. Use `Notion:notion-search` on the Tasks DB with the project name as query
2. For each task returned, use `Notion:notion-fetch` to retrieve: Task Name, Status, Assign, Due Date
3. Group tasks by project, display in step-number order

**Task status legend:** ✅ Done · 🔵 In Progress · 🟠 On Hold · 🟣 To Review · ⬜ Not Started · ❌ Cancelled

**Notion task naming convention (suffix key):**
- No suffix (e.g. `3- Costing Drawing`) → linked to Messung SHE'26
- `(1)` suffix (e.g. `3- Costing Drawing (1)`) → linked to Mosil IDMC'26
- `(2)` suffix → 3rd project, etc. Always verify via the `Project` field on the task page.

### Step 3 — Display Task Table Per Project

```
PROJECT: [Customer] | [Exhibition] | [Show Date] | [Venue]
SP: ₹X | Exec: [Name] | Days to show: [N]
Notion: [URL to project page]

| # | Task | Status | Assigned | Due Date |
|---|------|--------|----------|----------|
```

### Step 4 — Flag Critical Path Items

After each project's task table, output a FLAGS block:

```
⚠️ FLAGS — [Project Name]
- [Any task In Progress that should be Done given days remaining]
- [Any Due Date fields that are blank]
- [Any Priority fields that are unset]
- [Any missing Budget / Fabricator fields on the project card]
- [Any task past step 10 that is still Not Started with <30 days to show]
```

**Critical path rules:**
- **>30 days to show:** Tasks 1–8 should be Done or In Progress
- **15–30 days to show:** Tasks 1–12 should be Done; 13–16 In Progress
- **<15 days to show:** Tasks 1–19 should be Done; 20+ In Progress
- **<7 days to show:** Everything up to task 20 must be Done — flag any that aren't as URGENT

**Mandatory checks on every project card:**
- Budget field blank → `⚠️ Budget not set on Notion project card — margin not trackable at project level.`
- Fabricator field blank → `⚠️ Fabricator not recorded on project card — Doha Protocol compliance gap.`

### Step 5 — Production Summary Footer

```
PRODUCTION SUMMARY | FY26-27 | [Date]
Active projects: [N] | Total SP: ₹[X] | Closest deadline: [Project] in [N] days
Open flags: [N critical] | Tasks with no due date: [N]
```

### Notion 31-Step Task Reference

| Step | Task |
|---|---|
| 1 | Proforma Invoice to Customer |
| 2 | Advance Received from Customer |
| 3 | Costing Drawing |
| 4 | Fabricator Finalisation |
| 5 | Advance to Fabricator |
| 6 | Internal Execution Meeting |
| 7 | Technical Drawing |
| 8 | Fabricator Meeting |
| 12 | Security Deposit |
| 13 | Material Approval |
| 14 | Mockup |
| 15 | Onsite Schedule from Fabricator |
| 16 | Travel Expense Approval |
| 17 | Crew Travel Booking |
| 18 | Graphics & Logo Checking |
| 19 | Graphics & Logo to Fabricator |
| 21 | Possession Pics |
| 22 | Handover Pics |
| 23 | Dismantling Pics |
| 25 | Feedback Meeting with Customer |
| 27 | Final Invoice to Customer |
| 30 | Feedback Meeting with Fabricator |
| 31 | Final Payment to Fabricator |

### 5.3 — Receivables Priority (March 2026)

| Client | Amount | Priority |
|---|---|---|
| Secure — Bharat Electricity Show | ₹23,01,000 | #1 URGENT |
| TOTO | ₹5,79,478 | #2 |
| Elliott Ebara (LNG '26 Doha) | ₹5,71,215 | #3 — Settlement agreed: $11,074 to be paid, $3,225 written off |
| Labguard — CPhI | ₹5,22,169 | #4 |
| Spectrum | ₹1,69,000 | #5 |
| **Total** | **₹41,42,862** | |

**Payment terms (standard):** 90% on execution of agreement. 10% on handover.
**Cash lag:** Payment typically received 30–60 days after project completion.
**Indian corporate tax:** Effective rate 26% (25% + 4% cess). Tracked separately by Sonal. No current liability at confirmed pipeline levels. Advance tax schedule: 15 Jun (15%), 15 Sep (45%), 15 Dec (75%), 15 Mar (100%).

---
## SECTION 17 — STANDING COMMANDS

### "Production"
Execute Section 14 in full. No preamble. Output begins immediately.

### "Pipeline"
Display month-wise FY26-27 pipeline from CRM memory. Format:

| Customer | Show | Sqm | SP (₹) | Stage | Contact |

Then output: Stage summary · Secure Meters concentration % · Full year SP total.
Source: CRM data (last captured 10 Mar 2026). Flag if data is stale.

### "ABM"
Display full ABM target list industry-wise. No preamble. Format:

| Industry | Company | Tier | Contact Name | Designation | LinkedIn | Show Source | Status |

Groups: (1) Electrical/Energy (2) Architecture/Interior (3) Construction Machinery
Status values: Not Started · LinkedIn Connected · Email Sent · Meeting Booked · Proposal Sent · Won · Lost

### "MIS"
Display critical finance dashboard from MIS data. Show:
1. Liquidity & Runway (at ₹26L burn)
2. Receivables priority
3. Monthly burn vs contribution alerts
4. Client concentration check
5. Active alerts

Burn = ₹26L. Runway alert < ₹78L cash. Source: MIS files, not email summaries. No preamble.

### "Refresh CFO Matrix"
Execute this sequence:
1. Search Gmail for payment, invoice, credited, debited alerts from the last 7 days
2. Search Gmail for client names: Secure, Amaara, Elliott, Klenzaids, Labguard, Nordex, Gerresheimer, Iberchem, TOTO, Mosil, Messung, Truetzschler
3. Check Google Calendar for upcoming business meetings (next 14 days)
4. Read `/mnt/project/firstrain_cfo_v3_charts.jsx` from project files
5. Update STATIC_ALERTS, RECEIVABLES, and pipeline/client changes based on live data
6. Render the updated dashboard as an artifact using the JSX
7. Output a plain-text summary of what changed

---
