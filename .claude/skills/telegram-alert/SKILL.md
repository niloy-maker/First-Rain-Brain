---
name: telegram-alert
version: "1.0"
description: >
  Send an alert or summary to Niloy via Telegram. Run when a margin
  gate fails, cash drops below threshold, a receivable is critically
  overdue, Mangesh is blocking a concept, or any other urgent flag
  needs to reach Niloy immediately outside of a session.
---

# Telegram Alert — First Rain OS

## Purpose
Push urgent alerts to Niloy's Telegram (@FirstRainOS_bot) without
waiting for the next Claude Code session.

## Credentials
Load from `_context/telegram-config.md` — never hardcode in outputs.

## When to trigger (auto-surface these)
| Trigger | Priority |
|---|---|
| Margin gate FAIL on any quote | 🔴 Immediate |
| Operating cash < ₹76.5L | 🔴 Immediate |
| Receivable >45 days overdue | 🔴 Immediate |
| Secure concentration increases above 52.5% | 🔴 Immediate |
| Mangesh unavailable — concept blocked | ⚠️ Same day |
| Shilpa assigned field task (system blocked it) | ⚠️ Same day |
| Weekly report compiled and ready | ✅ Informational |
| Messung brief gaps still outstanding | ⚠️ Same day |
| Pankaj report not found in Crossnibble folder when /schedule runs | ⚠️ Same day |
| Target show within 90 days with no ABM outreach started | ⚠️ Same day |

## Message rules — INSTANT ALERTS ONLY
- Under 300 characters
- Lead with emoji: 🔴 urgent / ⚠️ warning / ✅ informational
- Include: what, which client/project, what action needed
- Never include SP/CP/margin numbers in plain text (internal only)
- This 300-character rule applies to instant alerts only — NOT to /monday or /schedule briefings

## How to send

Use the `mcp__plugin_telegram_telegram__reply` MCP tool directly:

```
chat_id: "8770250893"
text: "[your alert text]"
format: "text"
```

IMPORTANT: Always use this MCP tool. Never use a Python script or the Telegram HTTP API — the bot token in telegram-config.md is for an old bot (@FirstRainOS_bot) that is no longer active. The MCP plugin uses @FirstRainOS1_bot which is the live channel.

## Standard alert templates

### Margin FAIL
```
🔴 MARGIN FAIL — [Client] / [Show]. CM [X]% below [33/38]% floor. Reprice or walk. Check _outputs/finance/
```

### Cash alert
```
🔴 CASH ALERT — Operating ₹[X]L. Below ₹76.5L threshold. Sonal to advise.
```

### Receivable critical
```
⚠️ RECEIVABLE — [Client] ₹[X]L overdue [N] days. Chase brief in _outputs/finance/
```

### Weekly report ready
```
✅ W[N] report compiled. Open Claude Code and run /monday.
```

### Concept blocked
```
⚠️ DESIGN BLOCKED — [Client] concept waiting Mangesh review. [Show date] approaching.
```

### Pankaj report missing
```
⚠️ NO PANKAJ REPORT — Crossnibble folder empty. Chase Pankaj to upload weekly report.
```

### Show approaching, no outreach
```
📅 SHOW ALERT — [Show name] in [N] days. No ABM outreach started. Run /schedule.
```

## Guardrails
- Never send client-confidential data (SP, CP, margin %) via Telegram
- Never send PO numbers, bank details, or vendor pricing
- Always read telegram-config.md for credentials — never store token in output files
- If send fails → log to _outputs/telegram-failed-[date].md and tell Niloy in-session
