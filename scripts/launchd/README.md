# launchd agent scripts

Canonical **source-of-truth** copies of the shell scripts that back the four
scheduled tasks (morning sync, heal check, midday refresh, EOD refresh) plus
the watchdog reconciler.

## Files

- `firstrain-scheduled-task.sh` — invoked by each `com.firstrain.sched-*` launchd
  agent. Runs `claude --print` with the SKILL, delivers the resulting outbox
  to Telegram (with chunking for messages > Telegram's 4096-char cap), opens
  the dashboard in Chrome, and writes the day's marker so the watchdog knows
  the slot has fired.
- `firstrain-watchdog.sh` — invoked every 30 min by `com.firstrain.sched-watchdog`.
  Reconciles missed / failed task runs (cap 3/day per task), re-delivers stuck
  Telegram outbox messages, and only alerts as a last resort.

## Deploy target

Each script must live at `~/bin/` on the Mac that runs the launchd agents:

```
~/bin/firstrain-scheduled-task.sh
~/bin/firstrain-watchdog.sh
```

Both must be `chmod +x`. The plists at
`~/Library/LaunchAgents/com.firstrain.*.plist` invoke these paths.

## Sync workflow

When you change a script:
1. Edit the copy in `~/bin/` (that's what launchd actually runs).
2. Copy it into this folder and commit — this repo copy is the recoverable source.
3. When re-provisioning a Mac: `cp scripts/launchd/*.sh ~/bin/ && chmod +x ~/bin/firstrain-*.sh`.

## Guarantees these scripts must maintain

- **Telegram delivery must chunk** any outbox > 3900 chars on blank-line boundaries and send each part sequentially. All parts must confirm `ok:true` for `rc=0`.
- **Never silently truncate briefing content** — briefings genuinely need the length.
- **Return non-zero if delivery failed** so the watchdog can pick it up on the next tick.
- **Always resolve `api.telegram.org` via public DNS** (1.1.1.1 / 8.8.8.8) then pin the IP via `curl --resolve` to survive ISP-level DNS poisoning (learned 2026-06-16).
