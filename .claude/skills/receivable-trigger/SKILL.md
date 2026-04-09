---
name: receivable-trigger
version: "1.0"
description: >
  Generate a receivable chase brief for Sonal at project handover or when
  payment is overdue. Run when handover, final payment, balance due, chase
  payment, collections, overdue, receivable, outstanding, or "time to invoice
  [client]" is mentioned. Also run when a show closes and final billing is due.
---

# Receivable Trigger — First Rain

## Reference files
- `_context/clients.md` — payment terms per client, exec owner
- `_context/financial-rules.md` — receivables priority list, cash position
- `_context/active-projects.md` — confirm project status
- `_context/brand-voice.md` — for the chase message draft (direct, data first)

## Default payment terms (override from clients.md if client-specific)
- Standard India: 90% on agreement (advance), 10% on handover
- International: case-by-case, see `clients.md`
- Elliott Ebara: **PO required before Closed Won** — verbal ≠ revenue, always

## Inputs to collect
1. Client name (look up in clients.md)
2. Show name + date
3. SP (total)
4. Amount already received (advance / milestone payments)
5. Balance outstanding
6. Handover status — already done? scheduled? or overdue?
7. Any client context — silence, dispute, cash issue mentioned?

If handover hasn't happened yet → this is a **pre-trigger**, generate a reminder only.
If handover is done → this is a **live chase**, generate full brief for Sonal.

## Output format — always exactly this

```
RECEIVABLE TRIGGER — [Client] · [Show]

Exec: [Name from clients.md]
SP total: ₹[X]L | Received: ₹[Y]L | OUTSTANDING: ₹[Z]L
Due date: [date — standard = handover + 15 days, or per clients.md]
Days overdue: [0 if not yet due, else count]

Priority ranking: [#1–5 against current receivables list in financial-rules.md]
Cash impact: [what this unlocks — e.g. "covers X days of burn"]

CLIENT RULES APPLIED:
[Any special rule from clients.md — e.g. Elliott Ebara PO-first, Amaara blended 33%, etc.]

CHASE BRIEF FOR SONAL:
- Last contact: [date — ask if unknown]
- Next action: [specific — call/email/visit]
- Who owns it: [Sonal + exec named above]
- Escalation trigger: [if not cleared by [date], escalate to Niloy]

DRAFT CHASE MESSAGE (via /ghost style — direct, <80 words WhatsApp / <150 words email):
---
[Contact name] —
[One line: state the amount + context]
[One line: what's needed from them]
[One line: confirm date]
—
```

## Rules
- Never generate a chase without confirming the amount against `clients.md` or `active-projects.md` first
- If client has an active strategic exception (e.g. Amaara CM 17.6%), still chase the ₹ amount — the exception is on margin, not on payment
- For Elliott Ebara: if there is NO PO, this is not a chase — it is an escalation. Reply: "PO-first rule. Do not chase payment until PO exists. Flag to Niloy."
- For Secure Meters: note the 52.5% concentration — chase as normal, but include the concentration flag in Sonal's brief
- Never draft a legal/demand letter. Escalation stops at Niloy.

## Output destination
- Save brief to: `_outputs/receivable-[client]-[YYYY-MM-DD].md`
- Tag Sonal as owner, exec named in `clients.md` as second owner
- Update `_context/financial-rules.md` receivables priority table if priority changes

## Priority ladder (cross-reference financial-rules.md)
Current top 5 (April 2026):
1. Amaara Vitafoods ₹34L — doubles operating cash
2. Elliott Ebara LNG ₹10.23L — expected 2–7 May
3. Secure BES ₹6.3L — chase active
4. Messung ₹3.93L — April
5. Mosil ₹1.5L — April

If the new receivable outranks any of these → re-rank and flag to Niloy.
