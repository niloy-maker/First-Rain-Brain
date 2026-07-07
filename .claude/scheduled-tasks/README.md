# scheduled-tasks — canonical copies

Repo copies of the four scheduled task SKILLs. **Live copies** that launchd
actually invokes live at `~/.claude/scheduled-tasks/<task>/SKILL.md` — those
are what runs. This folder is the recoverable source-of-truth in case the
Mac is replaced or the local files get corrupted.

## Sync workflow

When you edit a SKILL:
1. Edit the live copy at `~/.claude/scheduled-tasks/<task>/SKILL.md` — that's
   what launchd/watchdog actually reads at fire time.
2. Copy the file into this folder and commit — repo copy is recoverable source.
3. When re-provisioning a Mac:
   ```bash
   cp -R .claude/scheduled-tasks/* ~/.claude/scheduled-tasks/
   ```

## Non-negotiable guarantees these SKILLs must maintain

### Morning sync (Step 5A)

- **COQL must SELECT Project_Month** — the by-project-month execution
  coverage strip depends on it. Dropped 2026-07-07, blanked the strip
  silently until fixed. Heal-check STEP 4C now watchdogs this.
- **Python transform must extract `project_month`** into each deal AND
  set `meta.project_month_available: True` — otherwise `run_pipeline.py`
  re-classifies from raw.json (without the field) and wipes downstream state.
- **Fall back gracefully** if Zoho reports the column missing: retry
  COQL without `Project_Month`, log to DATA HEALTH, do NOT abort.

### Heal-check STEP 4C

- Reads `FR.pipelineCoverageMeta.dataAvailable` — false is P0.
- Grep-canaries the morning-sync SKILL for the literal token `Project_Month`
  so a future edit that drops it fires an alert immediately.

### Watchdog / driver

- See `scripts/launchd/README.md` for the launchd shell scripts.
