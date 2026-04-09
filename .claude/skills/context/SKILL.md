---
name: context
version: "1.0"
description: Load First Rain context at the start of every session. Run when session starts, or when asked for a briefing, status update, or morning summary.
---

# Context Loader — First Rain V2

## Steps (in order)
1. Read CLAUDE.md
2. Read _context/active-projects.md
3. Read _context/decision-log.md
4. Read _context/session-log.md (last 3 entries only)

## Output — say exactly this
"First Rain V2 loaded.
[N] active projects. Last session: [date from session-log].
Top priority: [#1 urgent item from active-projects.md].
Active alerts: [any margin, concentration, or runway flags].
What are we working on?"

## Never skip the alerts line
If operating cash below ₹76.5L — say RUNWAY ALERT.
If Secure Meters above 25% of pipeline — say CONCENTRATION ALERT.
If any active project under 7 days to show — say URGENT: [project name].
