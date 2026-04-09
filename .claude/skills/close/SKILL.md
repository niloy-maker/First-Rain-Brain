---
name: close
version: "1.0"
description: End of session log. Run when session is ending, work is done for the day, or Niloy says done, closing, end session, wrap up.
---

# Session Close — First Rain V2

## Step 1 — Ask
"What happened today? Give me 3–5 bullets."
Wait for answer.

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
