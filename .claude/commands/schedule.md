# /schedule — First Rain Growth & Campaigns Weekly Briefing
# MESSAGE FORMAT: Full briefing — no character limit. 300-char rule applies to instant alerts only (telegram-alert skill).

Runs all 3 functions in sequence:
1. Ingest Pankaj's weekly campaign report from Google Drive
2. Analyse FirstRain-Intel for target shows (90–120 days) + ICP account recommendations
3. Send consolidated output to Telegram AND email to niloy@firstrain.co.in

Also runs automatically inside monday-sync every Monday.

---

## STEP 1 — Find Pankaj's latest report

Search Google Drive folder `13Wd4hJ9HIm3f2CbgwWh_dROijODDhLWQ` (FirstRain-Weekly-Reports/Growth/Crossnibble/) for the most recently modified file.
Use api_query: `'13Wd4hJ9HIm3f2CbgwWh_dROijODDhLWQ' in parents`
Order by: `modifiedTime desc`. Take the first result.
Note: file name, modified date, URI.

---

## STEP 2 — Fetch and extract campaign data

Fetch the file. If readable (Google Sheets), extract:

**Weekly Leads sheet:** Week of date · leads by channel (Google Ads, Organic, Email, WhatsApp, Calling, LinkedIn, Referral) · grand total · ICP qualified · meetings booked

**Google Ads Weekly sheet:** spend · conversions this week vs last week · CPA · top ad group · actions taken

**SEO Weekly sheet:** impressions + clicks (this week vs last week) · topics published

**ABM Outreach sheet:** shows in pipeline · contacts extracted · outreach sent · replies · meetings booked

**Task Tracker sheet:** done / total / blocked counts

If unreadable (xlsx): note filename + date. Flag: "Ask Pankaj to re-upload as Google Sheets."
If no file: note "No Pankaj report this week."

---

## STEP 3 — Analyse FirstRain-Intel for shows (90–120 days out)

### 3a — Load context
Read _context/abm-accounts.md (13 sectors + ABM target groups).
Read _context/icp-rules.md (ICP criteria: sector, company size, geography, show type).

### 3b — Scan show calendar
Read FirstRain-Intel/raw/show-calendar-fy2627.md.
Find all shows with dates between TODAY + 90 days and TODAY + 120 days.

For each show in that window:
- Note: show name, date, city/venue, sector tag (if present)
- Match to one of the 13 ABM sectors from abm-accounts.md:
  1. Smart Metering  2. Energy  3. HVAC  4. Aluminium Doors/Windows
  5. Pharma  6. AV/Tech  7. Nutraceuticals  8. Beauty/Fragrance
  9. Rail  10. Textile Machinery  11. Architecture/Building Materials
  12. Stones  13. Construction Machinery
- Flag shows with NO sector match as "Unclassified — Niloy to review"

### 3c — Deep Intel dive per show
For each matched show, check if a wiki page exists at:
FirstRain-Intel/wiki/shows/[show-name].md (or similar filename)

If the wiki page exists, read it and extract:
- Number of exhibitors listed
- Any company names that match ABM target accounts (abm-accounts.md Groups 1–3, or any named account)
- Any companies that match ICP criteria even if not yet in target list:
  - Sector match to one of 13 ABM sectors
  - India-headquartered OR international MNC with India presence
  - Likely exhibiting = marketing/brand investment signal

### 3d — Build ICP account recommendations per show
For each show (90–120 day window), produce:
- **Show:** [Name] — [Date] — [City]
- **Sector:** [ABM Group #]
- **Existing targets attending:** [names from abm-accounts.md if found in exhibitor list]
- **New ICP recommendations:** [up to 5 companies from exhibitor list that match ICP but aren't yet in abm-accounts.md — include why: sector + size signal]
- **Recommended action:** [e.g. "Start LI Warm-Up now — show is 95 days away. Assign: Pankaj"]
- **Outreach urgency:** 90–105 days = START NOW · 106–120 days = PLAN THIS WEEK

If no wiki page exists for a show: note "No Intel page — add exhibitor list to FirstRain-Intel/raw/ to unlock recommendations."

---

## STEP 4 — Compose Telegram message

Build the full Telegram message:

```
📊 *FIRST RAIN — GROWTH & CAMPAIGNS REPORT*
_[today's date]_

━━━━━━━━━━━━━━━━━━━━
📥 *LEADS THIS WEEK* (Pankaj report)
• Google Ads: [N] | Organic: [N] | Email: [N]
• WhatsApp: [N] | LinkedIn: [N] | Referral: [N]
• *Total: [N]* | ICP qualified: [N] | Meetings: [N]

💰 *GOOGLE ADS*
• Spend: ₹[N] | Conv: [N] (was [N]) | CPA: ₹[N]
• Best group: [name] | Actions: [summary or –]

🔍 *SEO*
• Impressions: [N] ([±]%) | Clicks: [N] | Topics published: [N]

📬 *ABM OUTREACH*
• Outreach sent: [N] | Replies: [N] | Meetings: [N]

✅ *TASKS:* [done]/[total] done | [N] blocked
━━━━━━━━━━━━━━━━━━━━
🎯 *TARGET SHOWS — 90 to 120 Days Out*

[For each show:]
📍 *[SHOW NAME]* — [Date] — [City]
Sector: [ABM Group] | Urgency: [START NOW / PLAN THIS WEEK]
• Existing targets: [names or "None found"]
• New ICP picks: [Company 1 (reason)] · [Company 2] · [Company 3]
• Action: [recommended next step]

[If no shows in window: "No shows in 90–120 day window."]
━━━━━━━━━━━━━━━━━━━━
🚨 *FLAGS*
• [Any shows with no Intel page — exhibitor list needed]
• [Any unclassified shows]
• [Pankaj report issues if any]
```

Send to chat_id `8770250893`.

---

## STEP 5 — Send email to Niloy

Create a Gmail draft to: niloy@firstrain.co.in

Subject: `First Rain Growth Report — [today's date]`

Body (plain text, not markdown — use dashes and line breaks):

```
First Rain — Growth & Campaigns Report
[today's date]
---------------------------------------------

PANKAJ WEEKLY REPORT
Week of: [date]

Leads:
- Google Ads: [N]
- Organic: [N]
- Email (Lemlist): [N]
- WhatsApp (Wati): [N]
- LinkedIn: [N]
- Referral: [N]
- TOTAL: [N] | ICP Qualified: [N] | Meetings Booked: [N]

Google Ads:
- Spend: Rs.[N] | Conversions: [N] (prev: [N]) | CPA: Rs.[N]
- Best ad group: [name]
- Actions taken: [summary or none]

SEO:
- Impressions: [N] ([+/-]% vs last week) | Clicks: [N]
- Topics published: [N]

ABM Outreach:
- Outreach sent: [N] | Replies: [N] | Meetings: [N]

Tasks: [done]/[total] done | [N] blocked

---------------------------------------------

TARGET SHOWS — 90 TO 120 DAYS OUT

[For each show:]
[SHOW NAME] | [Date] | [City]
Sector: [ABM Group] | Urgency: [START NOW / PLAN THIS WEEK]
Existing targets attending: [names or None found]
New ICP recommendations:
  - [Company 1] — [reason: sector + size signal]
  - [Company 2] — [reason]
  - [Company 3] — [reason]
Recommended action: [next step]

[If no shows: "No shows in 90-120 day window this week."]

---------------------------------------------

FLAGS
[List any: missing Intel pages / unclassified shows / report issues]

---------------------------------------------
Sent by First Rain Brain | /schedule
```

Note to Niloy after creating draft:
"Email draft created — check Gmail Drafts to review and send."

Note: If Gmail send tool becomes available, auto-send directly instead of creating a draft.

---

## STEP 6 — Confirm to Niloy

Output in session:
"✅ /schedule complete.
- Pankaj report: [ingested / not found / unreadable]
- Shows analysed (90–120 days): [N shows] across [N sectors]
- New ICP recommendations: [N accounts]
- Telegram: sent
- Email: draft created in Gmail — review and send"

If no file found in the Crossnibble folder:
"No Pankaj report in FirstRain-Weekly-Reports/Growth/Crossnibble/. Confirm Pankaj has uploaded."

---

## STEP 7 — Run /linkedin-content

After Steps 1–6 above are complete, run `/linkedin-content`.

Rules:
- Do NOT overwrite any existing schedule outputs from previous weeks
- LinkedIn outputs go to `_outputs/linkedin-content/` only — never into growth or other output folders
- Raw posts saved to `FirstRain-Intel/raw/linkedin/posts/` — separate from other raw intel
- Telegram summary for LinkedIn is sent by `/linkedin-content` itself — do not send a second message
- If `/linkedin-content` fails for any reason, note the failure in session output and continue — do not block the rest of /schedule

After `/linkedin-content` completes, add to the final /schedule session confirmation:
"- LinkedIn posts: [3 posts generated / failed — see output]"
