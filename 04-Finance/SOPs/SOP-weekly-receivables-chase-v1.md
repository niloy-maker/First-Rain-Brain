SOP: Run the weekly receivables chase cycle

Version: 1.0 | Created: 9 April 2026 | Owner: Sonal
Trigger: Every Monday morning before 11am. Also runs immediately after any project handover (use /receivable-trigger first).
Frequency: Weekly — Monday. Non-negotiable. Do not defer to Tuesday.

## Why this exists

Receivables left unchased past 30 days compound. At ₹25.5L monthly burn and operating cash at under 1 month, a single ₹34L backlog (Amaara, April 2026) threatens payroll. This SOP exists because informal chasing failed — this is the replacement.

## Prerequisites

- Access to Zoho Books (Finance > Receivables)
- Access to `_context/clients.md` — open before step 3
- WhatsApp access to all client contacts
- If a new project handed over last week: `/receivable-trigger` output already in `_outputs/` for that client
- No Niloy approval needed for steps 1–6. Escalation in step 7 requires Niloy's awareness, not approval.

## Steps

**Step 1.** Open Zoho Books → Reports → Outstanding Receivables. Run the report for all clients. Export or screenshot.

**Step 2.** Sort by "Overdue Days" descending. Note every invoice above 30 days overdue.

**Step 3.** For each overdue invoice: open `_context/clients.md` and read the client rule.
- Elliott Ebara entry? Check if PO exists. If no PO → do not chase → flag to Niloy immediately (PO-first rule, no exceptions).
- Secure Meters entry? Chase as normal but note the 52.5% concentration flag in your message to Niloy.
- All others → proceed to step 4.

**Step 4.** For each invoice above 30 days: draft a WhatsApp message in Niloy's voice using `/ghost`.
- Input to /ghost: client name, contact name, amount, number of days overdue, any known context
- Keep it under 80 words. One ask. Direct.
- Do not threaten. Do not apologise. State the amount and ask for a date.

**Step 5.** Send the WhatsApp. Log the send date and amount in a running note (WhatsApp itself is the record — screenshot if needed).

**Step 6.** Add a one-line entry to `_outputs/receivable-[client]-[date].md` if one exists, or create a new note: "Chased [date]. Awaiting response."

**Step 7.** Set a 72-hour reminder.
- If client responds with a date → note it, confirm to Niloy in the weekly update.
- If no response in 72 hours → forward to the exec owner (Chinmay / Shilpa depending on client) and ask them to follow up directly.

**Step 8.** Set a 7-day reminder from original send.
- If still no response after 7 days → escalate to Niloy. Send him: client name, amount, days overdue, what was sent, what exec did.
- Do not chase further yourself past this point. Niloy owns it from here.

**Step 9.** After all chases are sent: update the receivables table in `_context/financial-rules.md`.
- Update status column for each client chased.
- If any amount clears during the week → update the cash position line.
- Flag to Niloy if operating cash drops below ₹76.5L (3 months runway alert threshold).

## Definition of done

- Every invoice above 30 days has been actioned (chased, escalated, or PO-flagged)
- `_context/financial-rules.md` receivables table updated
- Niloy has a one-line summary in Monday's update: "Chased [N] clients. Total outstanding: ₹X. Highest risk: [Client]."
- Any PO-first violation flagged to Niloy before step 4 proceeds

## Failure modes to watch for

- **Skipping a week** → receivables slip to 45+ days, clients assume silence = no urgency. Never skip. If Sonal is absent, Ravindra runs steps 1–5 only and flags to Niloy.
- **Chasing without reading clients.md** → risks violating Elliott Ebara PO rule or misquoting an amount. Always read the client rule first.
- **Sending a wall of text** → clients ignore it. One amount, one ask, one sentence. Use /ghost.
- **Treating escalation as failure** → escalation at 72 hours is the system working, not a problem. Do not delay escalation to avoid difficult conversation.
- **Updating financial-rules.md with stale data** → always pull from Zoho Books, not memory. The file is only as good as the last Monday update.

## Escalation

If Elliott Ebara has no PO → escalate to Niloy immediately. Do not chase.
If any single client balance exceeds ₹20L and is 30+ days overdue → escalate to Niloy same day, do not wait 7 days.
If operating cash drops below ₹76.5L → escalate to Niloy immediately regardless of day of week.
Never draft a legal notice or demand letter. That decision belongs to Niloy only.

## Related skills / files

- Skill: /receivable-trigger — run this at handover before the Monday cycle
- Skill: /ghost — draft all chase messages through this
- Context: `_context/financial-rules.md` — receivables table + cash position
- Context: `_context/clients.md` — client-specific payment rules
- Context: `_context/team-map.md` — exec owner per client
