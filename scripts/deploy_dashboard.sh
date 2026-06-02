#!/bin/bash
# ============================================================================
# First Rain — Canonical dashboard deploy to Cloudflare Pages
# ----------------------------------------------------------------------------
# THE SINGLE SOURCE OF TRUTH for deploying dashboards/dashboard.html.
# Called identically by every path so they can never drift again:
#   - /finance Step 11        (.claude/commands/finance.md, interactive)
#   - first-rain-monday-sync  (9:08 AM cron, headless)
#   - first-rain-heal-check   (10:05 AM self-heal, headless)
#
# WHY THIS EXISTS: For weeks the headless crons ran a *copy* of the deploy
# command that was missing `source .secrets/cloudflare.env`, so wrangler had
# no CLOUDFLARE_API_TOKEN and every morning deploy failed -> Sonal saw a stale
# dashboard. The interactive copy (finance.md) sourced the env and worked, so
# the bug hid in plain sight. One script, called everywhere, kills that bug class.
#
# Exit codes (also written to data/projects/deploy_status.json):
#   0  OK      — new build is live and the password gate is responding
#   2  FAIL    — no token (file missing / token empty / revoked)
#   3  FAIL    — wrangler not found on PATH
#   4  FAIL    — dashboard.html missing, empty, or still contains a placeholder
#   5  FAIL    — wrangler deploy command errored
#   6  WARN    — deployed but canonical URL did not return the expected 401 gate
#
# The final stdout line is ALWAYS machine-parseable:
#   DEPLOY_RESULT=OK   url=<deploy_url> canonical=<http_status>
#   DEPLOY_RESULT=FAIL reason=<slug> detail="<human text>"
# The briefing/heal-check agents must report from THAT line + deploy_status.json,
# never invent a "headless gap" narrative.
# ============================================================================

set -uo pipefail

REPO="/Users/monicadebnath/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain"
PROJECT="firstrain-dashboard"
CANONICAL="https://firstrain-dashboard.pages.dev/"
STATUS_JSON="$REPO/data/projects/deploy_status.json"

# Layer 0 — guarantee Homebrew bins are on PATH. launchd's headless env ships a
# minimal PATH that excludes /opt/homebrew/bin, where wrangler/node/npx live.
# Without this the cron could fail with "wrangler: command not found" even with
# a perfectly valid token. (Latent second bug — fixed here pre-emptively.)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Emit the machine-parseable result, persist deploy_status.json, then exit.
# Usage: finish <exit_code> <result> <reason_slug> <human_detail> [deploy_url] [canonical_status]
finish() {
  local code="$1" result="$2" reason="$3" detail="$4" url="${5:-}" canon="${6:-}"
  mkdir -p "$(dirname "$STATUS_JSON")"
  cat > "$STATUS_JSON" <<EOF
{
  "result": "$result",
  "reason": "$reason",
  "detail": "$detail",
  "deploy_url": "$url",
  "canonical_status": "$canon",
  "checked_at_utc": "$TS",
  "exit_code": $code
}
EOF
  if [ "$result" = "OK" ]; then
    echo "DEPLOY_RESULT=OK url=$url canonical=$canon"
  else
    echo "DEPLOY_RESULT=FAIL reason=$reason detail=\"$detail\""
  fi
  exit "$code"
}

cd "$REPO" || finish 2 FAIL repo_missing "Repo path not found: $REPO"

# Layer 1 — TOKEN. Source the env file only if the token isn't already set,
# so an interactive shell that already exported it still works.
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  if [ -f "$REPO/.secrets/cloudflare.env" ]; then
    # shellcheck disable=SC1091
    source "$REPO/.secrets/cloudflare.env"
  else
    finish 2 FAIL no_token \
      "Missing .secrets/cloudflare.env — recreate token at https://dash.cloudflare.com/profile/api-tokens (Account > Cloudflare Pages > Edit) and write it there as 'export CLOUDFLARE_API_TOKEN=...'"
  fi
fi
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  finish 2 FAIL no_token \
    ".secrets/cloudflare.env present but CLOUDFLARE_API_TOKEN is empty — token likely revoked; recreate at https://dash.cloudflare.com/profile/api-tokens"
fi

# Layer 2 — wrangler must resolve.
if ! command -v wrangler >/dev/null 2>&1; then
  finish 3 FAIL no_wrangler "wrangler not on PATH ($PATH) — run 'npm i -g wrangler' or check Homebrew node install"
fi

# Layer 3 — never publish a broken or stale-placeholder dashboard to Sonal.
HTML="$REPO/dashboards/dashboard.html"
if [ ! -s "$HTML" ]; then
  finish 4 FAIL no_html "dashboards/dashboard.html is missing or empty — upstream build failed; refusing to deploy"
fi
if grep -q "{{CASHFLOW_JSON}}" "$HTML"; then
  finish 4 FAIL unsubstituted "dashboard.html still contains literal {{CASHFLOW_JSON}} placeholder — upstream build did not inject data; refusing to deploy"
fi

# Promote validated dashboard to the served index.
cp "$HTML" "$REPO/dashboards/index.html" || finish 4 FAIL copy_failed "Could not copy dashboard.html -> index.html"

# Layer 4 — deploy.
DEPLOY_OUT="$(wrangler pages deploy dashboards --project-name="$PROJECT" --branch=main --commit-dirty=true 2>&1)"
DEPLOY_RC=$?
if [ $DEPLOY_RC -ne 0 ]; then
  # Surface the most useful line of wrangler's error (auth errors mention "token"/"authentication").
  ERRLINE="$(echo "$DEPLOY_OUT" | grep -iE 'error|token|auth|forbidden|unauthor' | head -1 | tr -d '\r' | cut -c1-200)"
  finish 5 FAIL deploy_error "wrangler exited $DEPLOY_RC: ${ERRLINE:-see /tmp/deploy_dashboard.log}"
fi
DEPLOY_URL="$(echo "$DEPLOY_OUT" | grep -oE 'https://[a-z0-9]+\.firstrain-dashboard\.pages\.dev' | head -1)"
[ -z "$DEPLOY_URL" ] && DEPLOY_URL="$CANONICAL"

# Layer 5 — verify the live gate. Expected: 401 (the _worker.js Basic-Auth gate
# is alive and serving). 200 = gate bypassed (escalate). Anything else = not live.
CANON_STATUS="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$CANONICAL" 2>/dev/null)"
if [ "$CANON_STATUS" = "401" ]; then
  finish 0 OK ok "Deployed and gate live" "$DEPLOY_URL" "$CANON_STATUS"
else
  finish 6 WARN gate_unexpected "Deploy reported success but canonical returned HTTP $CANON_STATUS (expected 401) — verify Sonal can load it" "$DEPLOY_URL" "$CANON_STATUS"
fi
