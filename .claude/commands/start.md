## Step 0 — Load vault context
Read these three files in order:
1. `_context/active-projects.md`
2. `_context/decision-log.md` 
3. `_context/session-log.md` (last 3 entries only)

## Step 1 — Summarise in 5 bullets
1. 🔴 Active alerts (from financial-rules.md: cash, concentration, margin breaches)
2. 🔴 Receivables — top 3 by amount (from active-projects.md or financial-rules.md)
3. 🟠 Active projects — show date + days remaining (from active-projects.md)
4. 🟠 Open quote decisions (from active-projects.md)
5. 📝 Last session — date + key decisions made (from session-log.md)

Then say: "First Rain V2 loaded. What are we working on today?"

## Fallback — if _context/ files are missing
Warn: "⚠️ _context/ files not found. Is Claude Code pointed at the vault root?"
Check: `ls _context/` to verify the vault is the working directory.
