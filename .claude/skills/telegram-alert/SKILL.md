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

## Message rules
- Under 300 characters
- Lead with emoji: 🔴 urgent / ⚠️ warning / ✅ informational
- Include: what, which client/project, what action needed
- Never include SP/CP/margin numbers in plain text (internal only)

## How to send

```python
import urllib.request, urllib.parse, json

token = '[from telegram-config.md]'
chat_id = '8770250893'
message = '[your alert text]'

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = urllib.parse.urlencode({'chat_id': chat_id, 'text': message}).encode()
with urllib.request.urlopen(url, data) as r:
    result = json.loads(r.read())
```

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

## Guardrails
- Never send client-confidential data (SP, CP, margin %) via Telegram
- Never send PO numbers, bank details, or vendor pricing
- Always read telegram-config.md for credentials — never store token in output files
- If send fails → log to _outputs/telegram-failed-[date].md and tell Niloy in-session
