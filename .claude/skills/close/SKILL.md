---
name: close
version: "1.2"
description: End of session log. Run when session is ending, work is done for the day, or Niloy says done, closing, end session, wrap up.
---

# Session Close — First Rain V2

## Step 0 — Live data sync (ALWAYS run first, run all three in parallel)

### 0C — Finance data sync (from /finance JSON files)
- Read `data/projects/sheet_cash_position.json` (written by last /finance run)
- If file does not exist: skip silently, note "finance data not yet generated — run /finance first"
- If file exists: extract from the `cash` object:
  - `operatingCash` → current operating cash
  - `treasury` → treasury total
  - `odLimit` → OD facility
  - `odUtilized` → OD utilized
  - `hdfcLast4` → account identifier
  - `date` → when Sonal last updated
- Read `data/projects/sheet_receivables.json` for receivables list
- If `cash.operatingCash` differs materially from financial-rules.md: update cash figures
- No CSV fetch, no curl, no publish link — data comes from the last /finance run only

### 0A — Notion Production Tracker sync
Fetch the FR Production Tracker FY27 from Notion:
URL: https://www.notion.so/firstraingroup/ac84c676ad7249d2a79732d842f71d62

1. Search for all milestone rows in the database (use notion-search with "T0 T1 T2 T3 milestone production tracker")
2. Fetch each milestone page to read checkbox values for all active projects
3. For each project column, find the LAST milestone that is ticked (__YES__) — that is the current stage
4. Update the "Production Status" table in `_context/active-projects.md`:
   - ✓ = __YES__, ✗ = __NO__
   - Update "Last milestone reached" summary per project
   - Flag any project where show date is within 14 days and T21 (Installation Started) is not yet ticked
5. Update the `Last pulled:` date in the Production Status section

### 0B — Bigin pipeline sync
Pull latest "Sales Pipeline 26-27" data:
1. Query: `SELECT Deal_Name, Account_Name, Stage, Amount, Closing_Date FROM Pipelines WHERE Stage in ('Existing Confirmed', 'New Leads & Enquiries', 'BBANNTI Qualified', 'Closed Won 26-27') LIMIT 200 OFFSET 0`
2. Query: `SELECT Deal_Name, Account_Name, Stage, Amount, Closing_Date FROM Pipelines WHERE Stage in ('Design', 'Price Quote', 'Requirement gathering') LIMIT 200 OFFSET 0`
3. Compare against current `_context/active-projects.md`:
   - New Closed Won? → Add to "Executing now" table
   - Stage changed? → Update "Active quotes" / "Design stage" tables
   - New Existing Confirmed? → Add to pipeline table
4. Update the `# Last updated:` date at the top of `_context/active-projects.md` to today's date
5. If Secure concentration has changed materially, update alert in `_context/financial-rules.md`

## Step 1 — Daily Status Update (ALWAYS ask before logging)

Ask Niloy exactly this:

---
"Before I log the session — any updates to record?

💰 **Payments received today?** (e.g. Amaara ₹X, Elliott ₹X)
🏗️ **Project status changes?** (e.g. Labguard T21 ticked, Mosil advance paid)
📋 **Any other changes?** (new PO, exec assigned, quote approved)

Type them out or say 'none' to skip."
---

If Niloy provides updates:
1. Prepend each update as a new line to `_context/daily-updates.md` in the format:
   `[DATE] | [TYPE] | [DETAIL]`
   Types: RECEIVED / PAID / STATUS / NOTE
2. If a receivable is fully cleared, also update the receivables table in `_context/financial-rules.md` — mark amount as ₹0 and status as "Cleared [date] ✓"
3. If cash position changed materially, update the operating cash line in `_context/financial-rules.md`

If Niloy says 'none', skip to Step 2.

## Step 2 — Auto-generate session summary
Do NOT ask Niloy what happened. Derive 3–5 bullets from this session:
- Scan outputs created today (check `_outputs/` for files with today's date)
- Scan decisions made (any explicit approvals, instructions, or direction changes from Niloy)
- Identify what was unresolved or carries forward
Present the bullets to Niloy as a draft: "Here's what I've captured — confirm or correct before I log."

## Step 2 — Append to _context/session-log.md
---
Date: [today]
Key decisions: [bullets from Niloy]
Open items: [anything unresolved]
Next action: [clearest next step]
---

## Step 3 — Decision log
If today had a financial, client, people, or strategic decision:
Add one row to _context/decision-log.md.
Format: | [date] | [decision] | [rationale] | [owner] | [status] |
Otherwise do not add.

## Step 4 — Update autodream-memory.md
If any verified fact changed today (cash position, project status, client rule):
Update _context/autodream-memory.md with the new verified fact.

## Final output
"Session logged. [N] decision(s) added.
Tomorrow: [top open item].
Files written: session-log.md [+ decision-log.md if updated]."

## Rule
Write only to session-log.md, decision-log.md, autodream-memory.md.
No other files.
