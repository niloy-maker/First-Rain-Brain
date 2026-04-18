---
name: intel-lint
description: Health check for the FirstRain-Intel wiki. Finds broken links, past shows, stale account pages, and ingest gaps. Run monthly or on demand.
triggers: ["/intel-lint", "run intel health check", "check the wiki"]
---

# /intel-lint — Intel Wiki Health Check

When this skill is triggered, perform the following steps in order. Do not skip any step.

---

## Step 1 — Read the index

Read `FirstRain-Intel/index.md`.

Extract every `[[filename]]` Obsidian wiki link from the file. These are the pages that are supposed to exist.

For each link, determine what subfolder it belongs to based on which section of index.md it appears in:
- Links in the Shows sections → `FirstRain-Intel/wiki/shows/{filename}.md`
- Links in the Sectors section → `FirstRain-Intel/wiki/sectors/{filename}.md`
- Links in the Accounts sections → `FirstRain-Intel/wiki/accounts/{filename}.md`
- Links in the Competitors section → `FirstRain-Intel/wiki/competitors/{filename}.md`
- Links in the Fabricators section → `FirstRain-Intel/wiki/fabricators/{filename}.md`

Also extract the Month column value for each show row (e.g., "Apr 2026", "Jun 2026") — you'll need this in Step 3.

---

## Step 2 — Check for broken links

For every file path derived in Step 1, use the Read tool to check if the file exists.

If a file is listed in index.md but the .md file is not found on disk → flag as **BROKEN LINK**.

Keep a count: N_broken.

---

## Step 3 — Find past shows

Today's date is available from your context (check MEMORY.md or use 2026-04-18 if not set).

For every show link in index.md, read the Month value from the index table.
Parse the month string (e.g., "Apr 2026" → April 2026 → 2026-04-01 as a reference).
If that month has already passed relative to today → flag as **PAST SHOW**.

Shows in the current month are NOT past shows — only flag if the month is strictly before the current month.

Keep a count: N_past.

---

## Step 4 — Find stale account pages

For every account page listed in index.md (sections: "Accounts (Prospecting)" and "Accounts (Existing Clients)" and any other account sections):

Read the file and extract the `last_updated:` value from the YAML frontmatter.

If `last_updated` is more than 90 days before today → flag as **STALE ACCOUNT PAGE**.
If the field is missing entirely → flag as **STALE ACCOUNT PAGE (no date found)**.

Keep a count: N_stale.

---

## Step 5 — Check ingest recency

Read `FirstRain-Intel/log.md`.

Find the most recent date entry in the log table (format: `YYYY-MM-DD`).

Calculate how many days ago that ingest occurred relative to today.

If more than 30 days ago → flag as **NO RECENT INGEST**.
If 30 days or fewer → flag as **INGEST OK**.

---

## Step 6 — Output the report

Print the report in this exact format:

```
---
INTEL WIKI HEALTH CHECK — [today's date]

🔴 BROKEN LINKS ([N_broken] found):
  - [show/account name] — listed in index.md but file not found at [expected path]
  (if none: "  ✅ None found")

🟠 PAST SHOWS ([N_past] found):
  - [show name] — Month: [month]. Archive or delete?
  (if none: "  ✅ None found")

🟡 STALE ACCOUNT PAGES ([N_stale] found):
  - [account name] — last_updated: [date] ([N] days ago). Consider refreshing.
  (if none: "  ✅ None found")

[🟢 or 🔴] INGEST STATUS:
  Last ingest: [date] ([N] days ago)
  [OK — within 30 days] OR [OVERDUE — feed the wiki]

SUMMARY:
  Total links in index: [N_total]
  Broken links: [N_broken]
  Past shows (not yet archived): [N_past]
  Stale account pages (>90 days): [N_stale]
  Pages needing attention: [N_broken + N_past + N_stale]
---
```

---

## Step 7 — Save the report

Save the report to: `_outputs/intel-lint-[YYYY-MM-DD].md`

Tell Niloy: "Report saved to _outputs/intel-lint-[date].md. [Summary of top issues in one sentence.]"

---

## Rules

- This skill is READ ONLY. Do not edit, delete, or update any wiki files during a lint run.
- Do not attempt to fix the issues found — only report them.
- If index.md cannot be read, stop and say: "Cannot read FirstRain-Intel/index.md. Is the vault path correct?"
- Broken links take priority in the summary — list them first and flag them clearly.
