Update session records with key decisions from this conversation.

## Step 1 — Auto-generate session summary (do NOT ask Niloy)
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
