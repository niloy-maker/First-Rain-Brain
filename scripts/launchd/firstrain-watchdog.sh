#!/bin/bash
# FirstRain self-heal reconciler — the safety net AND auto-recovery for the 4 daily routines.
#
# WHY: launchd fires each routine ONCE/day. If that fire fails — claude socket drop
# (2026-06-08, 2026-06-16), shared-quota 429, or a delivery blocked by ISP DNS-hijack of
# Telegram (2026-06-16) — there was no same-day recovery: the old watchdog only ALERTED at
# 18:30, it never re-ran anything, and a closed-lid/off Mac skipped the day entirely.
#
# This is now a reconciliation loop (runs every ~30 min via StartInterval + RunAtLoad). Each
# cycle it converges actual state -> desired state. Desired, for every task past its slot:
#   (A) it COMPLETED today           -> a done-marker exists
#   (B) it DELIVERED its Telegram    -> no un-sent outbox file is left behind
# It heals each independently:
#   MODE A  re-runs a past-due task that has no done-marker, via the same driver (idempotent;
#           capped at MAX_RERUNS/task/day so a genuinely-broken skill can't burn tokens forever).
#   MODE B  re-delivers a COMPLETED task's outbox that the driver preserved after a failed send
#           (cheap — no skill re-run; just resend through the DNS-hijack-resilient sender).
# Niloy is alerted only as a LAST RESORT (re-run budget exhausted), deduped per task/day.
# Pure userspace — no sudo, no MCP, works headless.
#
# Fired by com.firstrain.sched-watchdog: StartInterval 1800 + RunAtLoad.
# Env: FRB_HEAL_DRYRUN=1 -> log every decision, take NO action (no re-run, no send).
set -u

VAULT_DIR="/Users/monicadebnath/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain"
DRIVER="/Users/monicadebnath/bin/firstrain-scheduled-task.sh"
LOG_DIR="$HOME/Library/Logs/firstrain"
DONE_DIR="$LOG_DIR/done"
ALERT_DIR="$LOG_DIR/watchdog-alerted"
ATTEMPT_DIR="$LOG_DIR/heal-attempts"
OUTBOX_DIR="$VAULT_DIR/_outputs/telegram-outbox"
LOG_FILE="$LOG_DIR/watchdog.log"
LOCK_DIR="/tmp/firstrain-self-heal.lock"
BOT_TOKEN="8624366986:AAG6h7Iu0BU4mfDMttr_e4bMGpZkR601pYw"
CHAT_ID="8770250893"
GRACE=40       # minutes after a slot before a missing run counts as failed (the fire + its
               # own internal retries take a while; don't pounce before they can finish)
MAX_RERUNS=3   # self-heal re-runs per task per day before escalating to a human alert
DRYRUN="${FRB_HEAL_DRYRUN:-0}"

# task:slot — keep in sync with the sched-*.plist StartCalendarInterval times
TASKS=(
  "first-rain-monday-sync:09:08"
  "first-rain-heal-check:10:05"
  "first-rain-midday-refresh:13:05"
  "first-rain-eod-refresh:18:08"
)

mkdir -p "$DONE_DIR" "$ALERT_DIR" "$ATTEMPT_DIR"
TODAY="$(date +%F)"
log() { echo "[$(date '+%F %T %Z')] [self-heal] $1" >> "$LOG_FILE"; }

send_telegram() {
  # DNS-hijack resilient + delivery-VERIFIED — mirrors firstrain-scheduled-task.sh (see
  # 2026-06-16: ISP poisoned api.telegram.org to a dead IP; the old urllib sender silently
  # timed out). Resolve via public DNS, pin the IP with curl --resolve, verify "ok":true,
  # retry. Returns 0 ONLY on confirmed delivery so callers can gate markers on real delivery.
  local msg="$1" ip body attempt=1
  ip="$(dig +short @1.1.1.1 api.telegram.org 2>/dev/null | grep -Eo '^[0-9.]+$' | head -1)"
  [ -z "$ip" ] && ip="$(dig +short @8.8.8.8 api.telegram.org 2>/dev/null | grep -Eo '^[0-9.]+$' | head -1)"
  [ -z "$ip" ] && ip="149.154.167.220"
  while [ "$attempt" -le 3 ]; do
    body="$(curl -s -m 25 --resolve "api.telegram.org:443:$ip" \
      --data-urlencode "chat_id=$CHAT_ID" \
      --data-urlencode "text=$msg" \
      "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" 2>>"$LOG_FILE")"
    if printf '%s' "$body" | grep -q '"ok":true'; then return 0; fi
    log "  telegram send attempt $attempt/3 failed (ip $ip): $(printf '%s' "$body" | head -c 120)"
    attempt=$((attempt+1)); [ "$attempt" -le 3 ] && sleep 15
  done
  return 1
}

# ── Single-instance reconciler lock (a re-run can take ~10m; never stack cycles) ──────────
if [ -d "$LOCK_DIR" ] && [ -n "$(find "$LOCK_DIR" -prune -mmin +45 2>/dev/null)" ]; then
  log "INFO — clearing stale self-heal lock (>45m old)."; rmdir "$LOCK_DIR" 2>/dev/null
fi
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "SKIP — another self-heal cycle is already running."; exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

now_min=$(( 10#$(date +%H) * 60 + 10#$(date +%M) ))
healed=0

# ── MODE B — re-deliver a COMPLETED task's outbox that a failed send left behind ──────────
# The driver preserves <task>.txt (does NOT move it to sent/) when its Telegram send fails,
# so a leftover today-dated outbox for a task whose done-marker EXISTS means: ran fine,
# delivery blocked. Resend it. (We require the marker so a partial outbox from a mid-run
# crash is never sent as if it were the final summary — MODE A re-run will rebuild that.)
if [ -d "$OUTBOX_DIR" ]; then
  for f in "$OUTBOX_DIR"/*.txt; do
    [ -e "$f" ] || continue
    base="$(basename "$f" .txt)"
    [ -f "$DONE_DIR/$base.$TODAY" ] || continue                       # only completed tasks
    [ "$(date -r "$f" +%F 2>/dev/null)" = "$TODAY" ] || continue      # only today's message
    if [ "$DRYRUN" = "1" ]; then
      log "DRYRUN — would re-deliver stuck outbox for $base ($(wc -c <"$f" | tr -d ' ') bytes)."; continue
    fi
    if send_telegram "⏰ DELAYED DELIVERY (self-heal) · $base · $TODAY
$(cat "$f")"; then
      mkdir -p "$OUTBOX_DIR/sent"
      mv "$f" "$OUTBOX_DIR/sent/$base.$TODAY.txt" 2>/dev/null
      log "REDELIVER — flushed stuck outbox for $base; delivery confirmed."
      healed=$((healed+1))
    else
      log "REDELIVER — $base outbox still undeliverable (network/DNS); will retry next cycle."
    fi
  done
fi

# ── MODE A — re-run a past-due task that never produced a done-marker ─────────────────────
for entry in "${TASKS[@]}"; do
  t="${entry%%:*}"; slot="${entry#*:}"
  due_min=$(( 10#${slot%%:*} * 60 + 10#${slot##*:} + GRACE ))
  [ "$now_min" -lt "$due_min" ] && continue                # not past due yet today
  [ -f "$DONE_DIR/$t.$TODAY" ] && continue                 # completed (delivery is MODE B's job)
  [ -d "/tmp/firstrain-task-$t.lock" ] && { log "WAIT — $t driver still running; not re-running this cycle."; continue; }

  acount="$(cat "$ATTEMPT_DIR/$t.$TODAY" 2>/dev/null)"; acount="${acount//[^0-9]/}"; [ -z "$acount" ] && acount=0

  if [ "$acount" -ge "$MAX_RERUNS" ]; then
    # Budget exhausted — escalate to a human, once, only if the alert actually delivers.
    [ -f "$ALERT_DIR/$t.$TODAY" ] && continue
    if [ "$DRYRUN" = "1" ]; then log "DRYRUN — would ESCALATE $t (exhausted $MAX_RERUNS re-runs)."; continue; fi
    if send_telegram "⚠️ FirstRain self-heal — '$t' failed and was auto-retried ${MAX_RERUNS}× today ($TODAY), still no result. Needs a human: open Claude Code and run it, or check ~/Library/Logs/firstrain/$t.log."; then
      : > "$ALERT_DIR/$t.$TODAY"; log "ESCALATE — $t exhausted $MAX_RERUNS self-heal re-runs; alerted Niloy."
    else
      log "ESCALATE — $t exhausted re-runs but alert delivery failed; will retry alert next cycle."
    fi
    continue
  fi

  if [ "$DRYRUN" = "1" ]; then
    log "DRYRUN — would re-run $t (slot $slot, attempt $((acount+1))/$MAX_RERUNS) via driver."; continue
  fi
  acount=$((acount+1)); echo "$acount" > "$ATTEMPT_DIR/$t.$TODAY"
  log "SELF-HEAL — re-running $t (attempt $acount/$MAX_RERUNS) via driver."
  /bin/bash "$DRIVER" "$t" "$slot" >> "$LOG_FILE" 2>&1
  if [ -f "$DONE_DIR/$t.$TODAY" ]; then
    log "SELF-HEAL — $t RECOVERED on attempt $acount (done-marker now present)."
    healed=$((healed+1))
  else
    log "SELF-HEAL — $t still failing after attempt $acount; will retry next cycle (≤$MAX_RERUNS)."
  fi
done

[ "$healed" -eq 0 ] && log "OK — nothing to heal for $TODAY (all past-due tasks done & delivered)."
exit 0
