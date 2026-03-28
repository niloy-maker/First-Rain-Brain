# /monday — First Rain Weekly Intelligence Briefing

Execute the following steps in order. Do not use more than 6 tool calls total.

## STEP 1 — Load Memory
Read MEMORY.md completely.
Note every item under:
- Active Alerts
- Receivables
- Active Projects
- Open Quote Decisions
- Last session's Running Log entry

## STEP 2 — Load Active Projects
Read P_Projects.md completely.
For each active project note:
- Customer name
- Show name and date
- Days remaining to show (calculate from today's date)
- Assigned exec

## STEP 3 — Check Gmail for Payment Alerts
Search Gmail for emails from the last 7 days containing:
payment, invoice, credited, debited, NEFT, RTGS

Also search Gmail for emails from these clients in the last 7 days:
Secure, TOTO, Elliott, Labguard, Spectrum, Amaara, Klenzaids, Nordex

## STEP 4 — Output the Weekly Briefing

Present in this exact format:

---
FIRST RAIN — MONDAY BRIEFING
Date: [today's date]
---

🔴 URGENT (action today)
- [List items that cannot wait]

🟠 THIS WEEK (action before Friday)
- [List items due this week]

🟡 WATCH (monitor only)
- [List items to monitor]

💰 RECEIVABLES UPDATE
- [Any payment news from Gmail]
- [Outstanding amounts]

🏗️ PROJECT STATUS
- [Each project: name, days to show, assigned exec]

📋 ONE ACTION PER FLAG
- [Flag] → Action: [next step] → Owner: [name]

---
NOTE: Notion task details not included here.
Type /production for full Notion task breakdown.
---