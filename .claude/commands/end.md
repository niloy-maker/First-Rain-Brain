Update session records with key decisions from this conversation.

Ask: "What happened today? Give me 3–5 bullets." Wait for response.

Then make exactly these changes:

**1. Append to `_context/session-log.md`:**
```
---
Date: [today] | Key decisions: [bullets] | Open items: [unresolved]
Next action: [clearest next step]
---
```

**2. If today had a financial, client, people, or strategic decision:**
Add one row to `_context/decision-log.md`. Otherwise do not add.

**3. Update `_context/autodream-memory.md`** with any verified fact changes
(numbers, receivables, project status, quotes confirmed).

**4. Update `_context/active-projects.md`** if any project status changed.

Show me the exact changes before saving. Wait for my approval.

After approval, save all changed files and run:
```
git add _context/session-log.md _context/decision-log.md _context/autodream-memory.md _context/active-projects.md
git commit -m "Session update: [date]"
git push origin main
```

Confirm when push is complete.
