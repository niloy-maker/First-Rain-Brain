#!/bin/bash
# FirstRain scheduled-task driver (launchd) — unified for all daily tasks.
#
# WHY: the in-app Claude Code scheduler only fires while a session is alive, so
# on a fresh boot / quiet morning the daily tasks silently never ran. This makes
# launchd the authoritative driver: it runs each task headless via `claude
# --print`, reusing the SAME single source of truth (the task's SKILL.md). The
# in-app copies of these tasks are DISABLED so nothing double-fires.
#
# Usage:  firstrain-scheduled-task.sh <task-id> <HH:MM>
#   <task-id> = dir under ~/.claude/scheduled-tasks/
#   <HH:MM>   = the task's scheduled local time (gates RunAtLoad catch-up)
#
# Behaviour:
#   - already ran today (marker present)  -> SKIP
#   - now < scheduled time                -> SKIP (a RunAtLoad fire before the
#                                            slot; the calendar fire will run it)
#   - otherwise                           -> run the SKILL headless, then mark
#                                            today done on success
# This gives: daily on-time runs (StartCalendarInterval), catch-up after a
# boot/wake that missed the slot (RunAtLoad), no early runs, no double runs.
#
# macOS TCC: this is launchd, so /bin/bash AND claude must have Full Disk Access
# (vault is under ~/Desktop). The plist must NOT set WorkingDirectory to the
# vault (that poisons file access); we cd here instead. See memory
# env_bashrc_claude_autolaunch.md.
#
# Env knobs: FRB_DRYRUN=1 -> log the decision, do not invoke claude.

set -u

TASK="${1:?usage: firstrain-scheduled-task.sh <task-id> <HH:MM>}"
SCHED="${2:?usage: firstrain-scheduled-task.sh <task-id> <HH:MM>}"

# ── Config ──────────────────────────────────────────────────────────────────
VAULT_DIR="/Users/monicadebnath/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain"
CLAUDE_BIN="/Users/monicadebnath/.local/bin/claude"
SKILL_FILE="$HOME/.claude/scheduled-tasks/$TASK/SKILL.md"
LOG_DIR="$HOME/Library/Logs/firstrain"
LOG_FILE="$LOG_DIR/$TASK.log"
DONE_DIR="$LOG_DIR/done"
LOCK_DIR="/tmp/firstrain-task-$TASK.lock"
BOT_TOKEN="8624366986:AAG6h7Iu0BU4mfDMttr_e4bMGpZkR601pYw"
CHAT_ID="8770250893"

# Per-task model + coalesced-fire ordering (audit 2026-06-10):
#   ALL tasks run on the default model (sonnet, from settings.json). Haiku was tried for
#   heal/midday/eod but it SHALLOW-EXITS these 24-38KB multi-MCP skills: on 06-10 the EOD
#   haiku run printed one sentence, exited rc=0 in 82s, and skipped the dashboard redeploy,
#   Chrome open and Telegram entirely (a false success). These skills need Sonnet to run to
#   completion. Real token savings would require trimming the skills, not downgrading the model.
#   PRIO = head-start (seconds) so that when a closed-lid Mac wakes and launchd fires all
#   four at once, they queue producer-first instead of racing (which caused false
#   "morning sync failed" alarms and shared-10k-tok/min 429s — see logs 06-08 / 06-10).
case "$TASK" in
  first-rain-monday-sync)     MODEL=""; PRIO=0  ;;
  first-rain-heal-check)      MODEL=""; PRIO=30 ;;
  first-rain-midday-refresh)  MODEL=""; PRIO=60 ;;
  first-rain-eod-refresh)     MODEL=""; PRIO=90 ;;
  *)                          MODEL=""; PRIO=0  ;;
esac
GLOBAL_LOCK="/tmp/firstrain-claude.lock"   # serialize every task's claude call -> one at a time, no shared-quota 429
# ─────────────────────────────────────────────────────────────────────────────

mkdir -p "$LOG_DIR" "$DONE_DIR"
TODAY="$(date +%F)"
MARKER="$DONE_DIR/$TASK.$TODAY"

log() { echo "[$(date '+%F %T %Z')] [$TASK] $1" >> "$LOG_FILE"; }

send_telegram() {
  # Deliver a Telegram message, resilient to ISP-level DNS hijacking of api.telegram.org.
  # On 2026-06-16 an Indian-telco DNS resolver poisoned api.telegram.org to a dead IP
  # (49.44.79.236) while Telegram itself stayed up at 149.154.x — the OS-resolver sender
  # silently timed out and the driver logged a FALSE "delivered" (no ok-check, no rc-gate).
  # Fix: resolve via PUBLIC DNS (1.1.1.1/8.8.8.8) and pin the IP with curl --resolve so the
  # ISP resolver can't poison it; then VERIFY the API returned ok:true; retry on failure.
  # Returns 0 ONLY on confirmed delivery — callers must gate "delivered"/move-to-sent on it.
  #
  # 2026-07-07: added CHUNKING. Telegram sendMessage rejects >4096 chars with
  # 400 "message is too long" and the whole delivery fails. Split the outbox on
  # blank-line boundaries (falls back to hard char-cut for run-on paragraphs)
  # and send each chunk sequentially. If any chunk fails, return 1 so the caller
  # marks the delivery as failed and preserves the outbox for retry.
  local msg="$1" ip
  ip="$(dig +short @1.1.1.1 api.telegram.org 2>/dev/null | grep -Eo '^[0-9.]+$' | head -1)"
  [ -z "$ip" ] && ip="$(dig +short @8.8.8.8 api.telegram.org 2>/dev/null | grep -Eo '^[0-9.]+$' | head -1)"
  [ -z "$ip" ] && ip="149.154.167.220"   # known-good Telegram fallback if public DNS also unreachable

  # Split into ≤3900-char chunks (headroom under the 4096 limit for URL encoding + suffix).
  local chunks
  chunks="$(printf '%s' "$msg" | awk '
    BEGIN { RS="\n\n"; ORS=""; buf=""; max=3900 }
    {
      block=$0 "\n\n"
      if (length(buf) + length(block) > max) {
        if (length(buf) > 0) { print buf "\x1F"; buf="" }
        while (length(block) > max) {
          print substr(block, 1, max) "\x1F"
          block = substr(block, max+1)
        }
      }
      buf = buf block
    }
    END { if (length(buf) > 0) print buf }
  ')"

  # Iterate chunks (separated by ASCII 0x1F "Unit Separator")
  local part=1 total idx=0 attempt body sub
  total=$(printf '%s' "$chunks" | awk 'BEGIN{RS="\x1F"; n=0} {n++} END{print n}')
  # Loop by splitting on 0x1F
  IFS=$'\x1F'
  for sub in $chunks; do
    idx=$((idx+1))
    # Prefix chunk-of-N marker when there's more than one part, so the reader knows it's split
    if [ "$total" -gt 1 ]; then
      sub="[part $idx/$total]"$'\n'"$sub"
    fi
    # Fail-fast: no chunk may exceed Telegram's 4096 limit (with a 96-char
    # safety margin for URL encoding). Better to log and abort loudly than
    # send-and-hope for a 400. This catches any regression in the chunker.
    if [ "${#sub}" -gt 4000 ]; then
      log "  telegram FATAL: chunk $idx/$total is ${#sub} chars, exceeds 4000 safety margin — chunker broken; aborting delivery"
      unset IFS
      return 1
    fi
    attempt=1
    local delivered=0
    while [ "$attempt" -le 3 ]; do
      body="$(curl -s -m 25 --resolve "api.telegram.org:443:$ip" \
        --data-urlencode "chat_id=$CHAT_ID" \
        --data-urlencode "text=$sub" \
        "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" 2>>"$LOG_FILE")"
      if printf '%s' "$body" | grep -q '"ok":true'; then
        delivered=1; break
      fi
      log "  telegram part $idx/$total send attempt $attempt/3 failed (ip $ip, len=${#sub}): $(printf '%s' "$body" | head -c 160)"
      attempt=$((attempt+1)); [ "$attempt" -le 3 ] && sleep 15
    done
    if [ "$delivered" -ne 1 ]; then
      unset IFS
      return 1
    fi
  done
  unset IFS
  return 0
}

# ── Already ran today? ────────────────────────────────────────────────────────
if [ -f "$MARKER" ]; then
  log "SKIP — already ran today ($MARKER)."
  exit 0
fi

# ── Due yet? (now >= scheduled). Blocks RunAtLoad fires before the slot. ───────
now_min=$(( 10#$(date +%H) * 60 + 10#$(date +%M) ))
sched_min=$(( 10#${SCHED%%:*} * 60 + 10#${SCHED##*:} ))
FIRE_HM="$(date +%H:%M)"   # when launchd actually fired this run — for the on-schedule report
if [ "$now_min" -lt "$sched_min" ]; then
  log "SKIP — not due yet (now $(date +%H:%M) < scheduled $SCHED); calendar fire will handle it."
  exit 0
fi

# ── Single-instance lock ──────────────────────────────────────────────────────
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "SKIP — another instance is already running (lock $LOCK_DIR)."
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT
[ -f "$MARKER" ] && { log "SKIP — marker appeared while acquiring lock."; exit 0; }

# ── Sanity ────────────────────────────────────────────────────────────────────
if [ ! -x "$CLAUDE_BIN" ]; then
  log "ERROR — claude binary missing at $CLAUDE_BIN."
  send_telegram "⚠️ FirstRain task '$TASK' could not run: claude CLI missing. Open Claude Code to run it manually."
  exit 1
fi
if [ ! -f "$SKILL_FILE" ]; then
  log "ERROR — SKILL missing at $SKILL_FILE."
  send_telegram "⚠️ FirstRain task '$TASK' could not run: SKILL file missing ($SKILL_FILE)."
  exit 1
fi

log "RUN — executing '$TASK' headless (scheduled $SCHED, now $(date +%H:%M))."

if [ "${FRB_DRYRUN:-0}" = "1" ]; then
  log "DRYRUN — would invoke: $CLAUDE_BIN --print (executing $SKILL_FILE). Not calling claude."
  exit 0
fi

PROMPT="You are running the First Rain scheduled task '$TASK' as a HEADLESS launchd job, because no interactive Claude Code session is open. Execute every instruction in the file ${SKILL_FILE} exactly and in order, to completion, without asking for confirmation. Today is ${TODAY}. This is an unattended run: rely on the durable connectors and the per-connector fallbacks defined in that file; if a connector needs interactive re-auth, log it and continue per the failsafe rules — do not abort. DELIVERY IS DRIVER-OWNED: after you finish, the launchd driver itself opens the dashboard in Chrome and sends the Telegram (reading _outputs/telegram-outbox/${TASK}.txt). Therefore you MUST still write the final Telegram message verbatim to that outbox file, but you MUST NOT run the skill's own dashboard Chrome auto-open step (labelled 5K in monday-sync, 5B-iv in midday/eod) — skip it so the dashboard does not open twice; just log that the driver will open it. A failed plugin:telegram MCP call is expected headless and is NOT an error — the driver delivers from the outbox."

cd "$VAULT_DIR" || { log "ERROR — cannot cd to vault ($VAULT_DIR). Likely missing Full Disk Access."; send_telegram "⚠️ FirstRain task '$TASK' could not access the vault (Full Disk Access?). Check ~/Library/Logs/firstrain/$TASK.log."; exit 1; }

# ── heal-check depends on monday-sync ─────────────────────────────────────────
# heal-check verifies that the morning briefing went out, so it must NOT judge
# monday-sync until monday-sync has actually FINISHED today (its marker is written
# only on success). Without this, a coalesced catch-up ran heal concurrently with
# monday-sync, read the half-built briefing stub, and fired a FALSE "sync failed"
# alarm (06-10). Wait up to 15m for the marker; if it never appears, monday-sync
# genuinely failed/never ran -> proceed and let heal report it truthfully.
if [ "$TASK" = "first-rain-heal-check" ]; then
  MS_MARKER="$DONE_DIR/first-rain-monday-sync.$TODAY"
  hwait=0
  while [ ! -f "$MS_MARKER" ] && [ "$hwait" -lt 900 ]; do
    log "WAIT — monday-sync not done yet today; holding heal-check (${hwait}s)."
    sleep 30; hwait=$((hwait+30))
  done
  if [ -f "$MS_MARKER" ]; then log "monday-sync marker present — proceeding with verification."
  else log "monday-sync marker ABSENT after ${hwait}s — proceeding; heal will report it as a real miss."; fi
fi

# ── Serialize claude across tasks (priority-ordered) — avoids the shared 10k tok/min 429 ──
# Clear a stale lock left by a crashed/killed run, then queue producer-first.
if [ -d "$GLOBAL_LOCK" ] && [ -n "$(find "$GLOBAL_LOCK" -prune -mmin +40 2>/dev/null)" ]; then
  log "INFO — clearing stale global claude lock (>40m old)."; rmdir "$GLOBAL_LOCK" 2>/dev/null
fi
sleep "$PRIO"
gwait=0; GOT_GLOBAL=0
while true; do
  if mkdir "$GLOBAL_LOCK" 2>/dev/null; then GOT_GLOBAL=1; break; fi
  if [ "$gwait" -ge 1800 ]; then log "WARN — global claude lock still held after 30m; proceeding without it."; break; fi
  log "WAIT — another FirstRain task holds the claude lock; holding (${gwait}s)."
  sleep 30; gwait=$((gwait+30))
done
trap 'rmdir "$LOCK_DIR" 2>/dev/null; [ "$GOT_GLOBAL" = 1 ] && rmdir "$GLOBAL_LOCK" 2>/dev/null' EXIT

log "INVOKE — claude --print${MODEL:+ --model $MODEL} (global-lock wait ${gwait}s, prio ${PRIO}s)."

# ── Bounded retry on transient API/network failure ────────────────────────────
# A daily task has only ONE calendar fire, so a single dropped socket / shared-quota
# 429 mid-run (e.g. "The socket connection was closed unexpectedly", rc=1) loses the
# whole day with no same-day recovery (the watchdog at 18:30 only alerts, never reruns).
# So retry the headless call up to MAX_ATTEMPTS with a short backoff. The GLOBAL_LOCK
# is intentionally held across all attempts — releasing between tries could let a
# sibling task start and reintroduce the shared 10k tok/min 429 this lock exists to
# prevent. We retry on ANY non-zero rc: a persistent failure simply exhausts the
# attempts and falls through to the same FAIL alert as before, just more robustly.
MAX_ATTEMPTS=3
RETRY_BACKOFF=60
attempt=1
while true; do
  echo "$PROMPT" | CLAUDECODE= "$CLAUDE_BIN" --print --dangerously-skip-permissions ${MODEL:+--model "$MODEL"} >> "$LOG_FILE" 2>&1
  RC=$?
  if [ "$RC" -eq 0 ]; then
    [ "$attempt" -gt 1 ] && log "RECOVERED — claude --print succeeded on attempt $attempt/$MAX_ATTEMPTS."
    break
  fi
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    log "claude --print exited rc=$RC on attempt $attempt/$MAX_ATTEMPTS — no retries left."
    break
  fi
  log "RETRY — claude --print exited rc=$RC on attempt $attempt/$MAX_ATTEMPTS (likely a transient API/socket drop); retrying in ${RETRY_BACKOFF}s."
  sleep "$RETRY_BACKOFF"
  attempt=$((attempt+1))
done
[ "$GOT_GLOBAL" = 1 ] && rmdir "$GLOBAL_LOCK" 2>/dev/null; GOT_GLOBAL=0   # release ASAP so the next task can start
log "claude --print exited rc=$RC"

if [ "$RC" -eq 0 ]; then
  : > "$MARKER"
  log "SUCCESS — '$TASK' completed; marked done for $TODAY."

  # ── Headless delivery (MCP-INDEPENDENT) ─────────────────────────────────────
  # The skills deliver Telegram via plugin:telegram MCP and open Chrome themselves,
  # but neither is reliable headless (the MCP isn't connected; a shallow model run may
  # skip both). So the driver owns delivery here, using the always-works python sender
  # and a local `open`. Skills write their final message to _outputs/telegram-outbox/.
  #
  # 1. Open the live dashboard in Chrome — canonical URL always shows the latest
  #    Production deploy, so no per-run staleness. Gate on a healthy deploy_status.
  #    ONLY for the dashboard-refreshing tasks; heal-check is a verifier and must not
  #    pop a tab. The skill's own auto-open (5K / 5B-iv) is suppressed via the driver
  #    PROMPT, so this is the single open per run.
  case "$TASK" in
    first-rain-monday-sync|first-rain-midday-refresh|first-rain-eod-refresh) OPEN_DASH=1 ;;
    *) OPEN_DASH=0 ;;
  esac
  DS="$VAULT_DIR/data/projects/deploy_status.json"
  if [ "$OPEN_DASH" != 1 ]; then
    log "Chrome: skipped — $TASK is a verifier, not a dashboard refresh."
  elif [ ! -f "$DS" ]; then
    log "Chrome: skipped — no deploy_status.json."
  else
    DRES="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("result",""))' "$DS" 2>/dev/null)"
    if [ "$DRES" = "OK" ]; then
      CANON="https://firstrain-dashboard.pages.dev/?t=$(date +%s)"
      if open -a "Google Chrome" "$CANON" 2>>"$LOG_FILE"; then log "Chrome: opened canonical dashboard."
      elif open "$CANON" 2>>"$LOG_FILE"; then log "Chrome: opened in default browser (Chrome unavailable)."
      else log "Chrome: open failed (no GUI session?); dashboard still live at $CANON."; fi
    else
      log "Chrome: skipped — deploy_status result='$DRES' (not OK)."
    fi
  fi

  # 2. Telegram — send the skill's outbox message (composed this run) via urllib,
  #    prefixed with an ON-SCHEDULE / LATE header so Niloy can confirm each routine
  #    fired on time (per 2026-06-10 request to verify routine-by-routine).
  LATE=$(( now_min - sched_min )); [ "$LATE" -lt 0 ] && LATE=$(( -LATE ))
  if [ "$LATE" -le 15 ]; then SCHED_LINE="🕐 ON SCHEDULE — $TASK fired $FIRE_HM (slot $SCHED) · $TODAY"
  else SCHED_LINE="⏰ LATE / CATCH-UP — $TASK fired $FIRE_HM (slot $SCHED, +${LATE}m) · $TODAY"; fi
  OUTBOX="$VAULT_DIR/_outputs/telegram-outbox/$TASK.txt"
  if [ -s "$OUTBOX" ] && [ "$(date -r "$OUTBOX" +%F 2>/dev/null)" = "$TODAY" ]; then
    if send_telegram "$SCHED_LINE
$(cat "$OUTBOX")"; then
      log "Telegram: delivered outbox message ($(wc -c <"$OUTBOX" | tr -d ' ') bytes) via driver. [$SCHED_LINE]"
      mkdir -p "$VAULT_DIR/_outputs/telegram-outbox/sent"
      mv "$OUTBOX" "$VAULT_DIR/_outputs/telegram-outbox/sent/$TASK.$TODAY.txt" 2>/dev/null
    else
      # Delivery genuinely failed (network/DNS). Do NOT move to sent/ and do NOT log a false
      # "delivered" — leave the outbox in place so it can be re-sent. The run itself succeeded.
      log "Telegram: DELIVERY FAILED after retries (network/DNS) — outbox PRESERVED at $OUTBOX for re-send."
    fi
  else
    if send_telegram "$SCHED_LINE
✅ '$TASK' completed at $(date +%H:%M). Dashboard refreshed. (Full summary in today's Gmail draft — no Telegram outbox file was written this run.)"; then
      log "Telegram: no fresh outbox — sent generic completion ping via driver. [$SCHED_LINE]"
    else
      log "Telegram: no fresh outbox AND generic ping failed to deliver (network/DNS)."
    fi
  fi
  # ────────────────────────────────────────────────────────────────────────────
else
  log "FAIL — '$TASK' rc=$RC (no marker written; will retry on next fire)."
  send_telegram "⚠️ FirstRain automated task '$TASK' failed today ($TODAY), rc=$RC — its usual update may not have gone out. Check ~/Library/Logs/firstrain/$TASK.log or open Claude Code."
fi

exit 0
