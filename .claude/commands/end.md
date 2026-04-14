Update session records with key decisions from this conversation.

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

## Step 2 — Auto-generate session summary (do NOT ask Niloy)
Derive 3–5 bullets from this session by scanning:
- Files written or edited today (check _outputs/ for today's date)
- Decisions Niloy made explicitly (approvals, instructions, direction changes)
- Anything unresolved or carrying forward

Present the draft to Niloy exactly like this and WAIT for approval:

---
"Here's what I've captured from today's session — confirm, correct, or add before I log:

**Key decisions:**
- [bullet 1]
- [bullet 2]
- [bullet 3]

**Open items:**
- [unresolved 1]
- [unresolved 2]

**Next action:** [clearest single next step]

**Decision log row (if applicable):** [one-line decision for decision-log.md, or 'None today']

Approve to commit? (yes / edit first)"

---

## Step 2 — After Niloy approves, make exactly these changes:

**1. Append to `_context/session-log.md`:**
```
---
Date: [today] | Key decisions: [bullets] | Open items: [unresolved]
Next action: [clearest next step]
---
```

**2. If today had a financial, client, people, or strategic decision:**
Add one row to `_context/decision-log.md`:
| [date] | [decision] | [rationale] | [owner] | [status] |
Otherwise skip.

**3. Update `_context/autodream-memory.md`** with any verified fact changes
(cash position, receivables, project status, client rules, new integrations).

**4. Update `_context/active-projects.md`** if any project status changed today.

## Step 3 — Git commit and push

After all files saved, run:
```
git add _context/session-log.md _context/decision-log.md _context/autodream-memory.md _context/active-projects.md
git commit -m "Session update: [date]"
git push origin main
```

Confirm: "Session logged. Pushed to GitHub. Tomorrow: [top open item]."

## Rules
- Never skip Step 1. Always show the draft and wait for Niloy's approval before writing anything.
- Never ask "What happened today?" — derive it from the session.
- Never commit without explicit approval ("yes" or equivalent).
- Write only to: session-log.md, decision-log.md, autodream-memory.md, active-projects.md.
