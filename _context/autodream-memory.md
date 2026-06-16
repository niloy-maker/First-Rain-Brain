# First Rain — autoDream Consolidated Memory
# Maintained by KAIROS autoDream during idle periods.
# Until KAIROS ships, /close updates this manually.
# Format: verified facts only. No vague notes. No contradictions.
# Last consolidated: 9 April 2026

## Verified client facts
- GIC India (gicindia.com): New target account. Electrical automation sector. GSTIN 27AAACG6241J1ZM, MIDC Bhosari Pune. Multi-show commitment: ELAsia Bangalore 36sqm + Automation India Mumbai 46sqm + Elecrama 2027 Gr. Noida 110sqm. Bundle pricing: ₹34.83L at 36.8% CM (5% loyalty). ELAsia Closed Won ₹6.50L SP (EST-26-27-03, ₹7.67L incl. IGST). Exec: Shilpa. T01 PI Sent ✓ (17 Apr). T02 advance pending. Zoho contact created 15 Apr 2026.
- Secure Meters: 41.5% of FY27 active pipeline (₹287.24L / ₹692.44L, 28 Apr). Ceiling 25%. Live breach.
  MEE ₹18.95L on hold. RenewX ₹9.4L awaiting PO (floor ₹7.24L).
  Utility Week: GH Display selected, GH10918/3 £16,319.75. PO required first.
  Utility Week: Doha Protocol — 3 FAIL (supervisor, GH paperwork, escalation contact). PO deadline 14 April.
  Utility Week: SP ₹42L / CP GBP at ₹125 = ₹20.4L → CM 43% PASS. Buffer: quote at ₹127-128/GBP.
- Amaara Vitafoods: ₹34L receivable — #1 cash priority. CM% unconfirmed. Contact: Karan. Exec: Shilpa.
- Amaara Wellness: ₹12L receivable, 45 days overdue. Entity unconfirmed — may be same as Vitafoods (combined ₹46L).
- Crompton Greaves: Active quote ₹18L SP / ₹11L CP. CM 38.9% PASS. New prospect — not yet in clients.md.
- Elliott Ebara: PO required before Closed Won. Verbal ≠ revenue. Receivable ₹10.23L — cleared 14 Apr 2026 ✓
- Messung: Smart Manufacturing Expo Pune brief received — ₹8L SP, 9 sqm, margin PASS. 5 brief gaps outstanding.

## Verified financial facts
- Monthly burn FY27: ₹25,50,000 | Operating cash: ₹12,58,919 (CRITICAL — 0.5 months) [updated 05 May from Sonal's sheet]
- Treasury: ₹1,39,95,068 | OD Facility: ₹1,21,00,000 | OD Utilized: ₹0
- Cash floor: ₹76,50,000. Current cash is 16% of floor — escalation level.
- Carl Bechem ₹1,16,800 received 15 Apr — BME Conclave post-show. HDFC XX0247 NEFT AXISP00788721946.

## Verified project facts
- Bechem BME Delhi 8–9 Apr: FULLY CLOSED. T27–T31 all ✓. [updated 05 May]
- Labguard Analytica 22–24 Apr: Show complete. T22/T23 ✓. T27 final invoice NOT sent. [updated 05 May]
- Mosil IDMC Lucknow 23–24 Apr: Show complete. T22/T23 ✓. T27 final invoice NOT sent. [updated 05 May]
- Messung Smart Home 28–30 Apr: Show complete. T22/T23 ✓. T27 final invoice NOT sent. [updated 05 May]
- Secure RenewX Chennai 27 Apr: Show complete. T22/T23 ✓. T27 final invoice NOT sent. [updated 05 May]
- Amaara Vitafoods Europe Barcelona 5–7 May: SHOW ON NOW. T20/T21 ✓. T22/T23 after close. ₹14L balance to chase.
- GIC ELAsia Bangalore 14–17 May: T15 ✓. T02 advance STILL NOT received. 9 days to show.
- Secure Utility Week Birmingham 19 May: Closed Won ₹47.95L. T01–T06 NOT set up in Notion. 14 days.
- Secure RenewX 27 Apr: Active. Exec: Chinmay. T06 ✓ — T02 advance NOT received. 12 days to show.
- Amaara Vitafoods Europe ~5 May: Active. Exec: Shilpa. T11 ✓. T08 still pending. ₹14L outstanding — required before on-site.
- GIC ELAsia Bangalore 14–17 May: Active (Closed Won 15 Apr). Exec: Shilpa. ₹6.50L SP. T01 PI Sent ✓ (17 Apr). T02 advance pending.

## Verified system facts
- Vault v6.1 operational: 6 department agents + orchestrator live and tested (system test passed 9 Apr)
- Orchestrator: single entry point, routes plain-language tasks to correct agent — tested with Messung brief
- Telegram: @FirstRainOS_bot live. Niloy chat ID 8770250893. Token rotated 9 Apr. /telegram-alert skill live.
- /end command: updated 10 Apr to auto-generate session bullets (no longer asks Niloy what happened)
- 08-Accounts: client and prospect files (renamed from 08-Clients 11 Apr). Clients = active/past projects. Prospects tagged "PROSPECT — Not yet a client". Secure-Meters as benchmark format.
- Zoho Books: proposals/estimation only. Tally is actual invoicing source of truth. All FY25-26 Zoho invoices are estimates. Zoho Books Estimates = source of truth for customer contact info.
- Scatterpie Analytics: TENANT. ₹2,12,400/month rent. Not exhibition client. Exclude from all revenue/CM% reporting.
- Kelegent Metaplast = Shree Mahavir Metal (renamed). Anand Engineers Private Limited = Molygraph (same entity in Zoho).
- FY25-26 verified: 24 exhibition clients, ₹6.01Cr billed in Zoho estimates. Only Neutral Glass (₹30.95L) confirmed paid.
- Google Drive FirstRain-Weekly-Reports/ live: Growth, Client-Delivery, Design, Finance, People subfolders created. Sonal uploads Finance report every Monday.
- /close skill: v1.2 — includes Notion production tracker sync + Bigin pipeline sync. Finance fetch: curl -L (not WebFetch — 307 redirect expires).
- Brief Studio: First Rain Design Briefs Google Sheet (1XjPUeYgIUHgSrgToZGqslQPR6rtM0Zc9y86zbLnwJYs, gid=365151360). Fetched via curl -L export. Wired into daily briefing Step 2B — summary table + synopsis. Apps Script URL (AKfycbz...) = Design Brief Studio UI, not a data endpoint.
- Sales call system (17 Apr): 5-step bootcamp output complete. Step 5 scripts live. Inbound BBANTI script live. All permission asks = "30 seconds".
- monday-sync scheduled task: Monday 11:00 AM IST — Notion + Bigin + Sonal's report + Zoho Books new customer check → active-projects.md update + Telegram alert
- FirstRain-Intel wiki: 241 show pages, 25 CPhI China Tier 1 accounts, 2 competitor profiles (Inoways added 9 Apr)
- Two sales hunters approved 8 Apr: Domestic (May), International (June). Domestic JD drafted 9 Apr.
- CPhI China campaign live: W1 tasks due Dhruv + Pankaj by 13 April
- As Built document created: _outputs/FirstRain-OS-AsBuilt-2026-04-10.md (for BenAI meeting)
- Brand voice (Exhibitions): fully rebuilt from StoryBrand BrandScript guide (Jan 2024). One-Liner, taglines, full framework in _context/brand-voice.md.
- Scheduled reminders: Sales Circle + regional pricing + tool stack review (20 Apr), LinkedIn content strategy (20 Apr), Interiors brand voice (1 Jul), competitive positioning review (1 Jul), Telegram team group chat decision (1 Jul 12:00).
- ICP geography updated: India (Mumbai · Bengaluru · New Delhi · Greater Noida · Hyderabad · Chennai). International (Europe · SE Asia · China · Middle East · UK new market).
- Dhruv removed from all campaign responsibilities (11 Apr). Pankaj (CrossNibble) = sole campaign owner (Tier 2 calls, Freckle, Lemlist, Wati, Google Ads). Bigin pipeline = Niloy only.
- /schedule skill live (.claude/commands/schedule.md): Pankaj Google Drive report ingest + FirstRain-Intel show analysis 90-120 days + ICP picks per show + Telegram briefing + Gmail draft to niloy@firstrain.co.in. Also embedded in monday-sync.
- Pankaj-Weekly-Report-Template.xlsx created: _outputs/Pankaj-Weekly-Report-Template.xlsx. 6 tabs (Weekly Leads, Google Ads Weekly, SEO Weekly, ABM Outreach, Task Tracker, Monthly Summary). Pankaj uploads to FirstRain-Weekly-Reports/Growth/Crossnibble/ on Google Drive. Must upload as Google Sheets format for auto-ingestion.
- Google Drive Crossnibble folder ID: 13Wd4hJ9HIm3f2CbgwWh_dROijODDhLWQ
- ABM sector list expanded to 13 sectors (11 Apr). Groups 1-3 fully populated (Electrical/Energy 18 accounts, Architecture/Interior 9 accounts, Construction Machinery 12 accounts). Groups 4-13 pending Niloy input.
- Telegram message rules: instant alerts ≤300 chars. /monday and /schedule briefings = full format, no character limit. New triggers: Pankaj report missing + show within 90 days no outreach started.
- monday-sync task updated (11 Apr): 9 steps — Notion + Bigin + Sonal report + Zoho Books + Pankaj report + show calendar Intel analysis (90-120 days) + update active-projects.md + Telegram + Gmail draft.
- Team update 11 Apr: Sonal = Commercial Manager. Santosh = Sr Production Manager. Shilpa = Sr Project Executive (promoted). Komal = left. Chinmay = leaving for MBA ~1 year — succession in progress.

## Verified system facts (continued)
- /proposal-maker v1.3 (15 Apr): IGST applied via tax_id on main line item only — never a separate tax line item. tax_id IGST18 (1389751000000365081) for inter-state. Default design option = "Exhibition Stall Design & Build as per submitted design". EST-26-27-03 is the reference for correct format.
- Zoho Books EST numbering: EST-26-27-01 (Amaara), EST-26-27-02 (Coats India test), EST-26-27-03 (GIC ELAsia).

- IBA (Indian Banks Association): New enterprise account. SIBOS Miami 2026, 192 sqm, Miami Beach Convention Centre, 28 Sept–1 Oct 2026. First pitch 24 April. Themes: "India: Resilient by Design" / "India: Leading the Fiscal Future". Exec: Chinmay. Rock #1 opportunity. International 38% CM floor.
- Daily briefing automation (first-rain-monday-sync): Runs unattended 9am IST every day. Finance sheet → Gmail → Telegram → Gmail draft. Write + Edit permissions in settings.local.json. Output: _outputs/briefing-YYYY-MM-DD.md.

## Verified facts (19 Apr 2026)
- BYSS Platinum enrolled: ₹1,59,999 + GST. Parantap Chowdhury 1:1 Done-For-You Sales Coaching, 12 weeks. Custom GPTs to be built for First Rain. No team size limit. Active.
- Sales bootcamp complete (Days 1-3 ingested): outputs in _outputs/sales-bootcamp/. Day 1: ICP + Lead Mgmt + BBANTI + Call Scripts. Day 2: VIBE + Follow-up 4 types + Objection Handling 5-step. Day 3: 4 lead gen channels + channel strategy.
- Lead gen channel decision (Parantap, Day 3): Niloy must cold call — explicit instruction. Primary: Cold Calls + Warm Outreach (Past Clients). Secondary: LinkedIn Content. Paid Ads continues.
- Finance (19 Apr, Sonal's sheet): Operating Cash ₹24,56,438 — BELOW ₹76.5L threshold. Treasury ₹1,39,97,287. Receivables: Amaara ₹14L, Secure BES ₹6.5L, Messung ₹4.64L, Elliott ₹93.8K, Mosil ₹63K. Total ₹26.7L.
- Notion sync (19 Apr): No new milestones since 18 Apr. Labguard T21 still NOT ticked — show was TODAY 22 Apr.
- BharatTex'26 300sqm — new deal in Bigin "Requirement gathering" stage. Large new prospect — qualify next session.
- Parantap Brief pending — all 3 days + 8 questions to be compiled next session.

## Flagged for Niloy review
- Git identity still Monica Debnath — run: git config --global user.name "Niloy Debnath"
- Amaara Wellness entity — confirm if same as Vitafoods before Sonal chases
- Secure Utility Week PO — WhatsApp Rahul. Deadline 14 April. 3 Doha items still open.
- Messung Smart Manufacturing: 5 brief gaps from Gitesh due 10 April
- Sales Hunter JD — review _outputs/people/jd-sales-hunter-domestic-2026-04-09.md and post by 14 April
- Dept leads: submit W16 Drive reports by Friday (first /weekly-report auto-compile Sunday)
- /portfolio-story: retest after Messung Smart Home closes 30 April
- Rock 2 repricing — below 40% by Q1 unlikely; raise reframe to Q2 at next L10

## Verified facts (21 Apr 2026)
- Cash position: Operating Rs11,54,623 (0.5 months runway — CRITICAL). Treasury Rs1,40,02,517. OD Rs1,21,00,000. Vendor payments Rs20L pending outflow. [Updated 21 Apr Sonal sheet]
- Total receivables: Rs33,74,505 (Sonal sheet 21 Apr). Breakdown: Amaara Rs14L, Labguard Rs7.03L, GIC Rs6.5L, Messung Rs4.64L, Secure RenewX Rs93.8K, Mosil Rs63K.
- Labguard Analytica 22-24 Apr: T20 + T21 both ticked (21 Apr). ON SITE. Show TOMORROW.
- Secure RenewX 27 Apr: T02 Advance Received ticked (21 Apr). Show in 6 days. T07-T21 still pending.
- Messung Smart Home 28-30 Apr: T14 Mock Up ticked (21 Apr). Show in 7 days.
- Amaara Vitafoods Europe ~5 May: T18 Graphics Check ticked. Rs14L outstanding.
- BharatTex26 300sqm: New large prospect. In Design stage Bigin. Rs40L SP target. 29 May closing.
- GIC ELECRAMA 2027: 130sqm Rs23.47L confirmed Existing Confirmed in Bigin. Feb 2027 show.
- PCM Railone brief: RailTrans 2026 Pragati Maidan, possession 26 Apr, 36sqm Bold & Graphic. Status New, no exec. URGENT.
- bypassPermissions set: .claude/settings.json defaultMode = bypassPermissions for this project (21 Apr).

## Verified facts (28 Apr 2026)
- Operating cash: ₹35,86,209 (Sonal, 24 Apr, account 0247 — unchanged). BELOW ₹76.5L floor. Breach still active. Treasury: ₹1,39,97,249. OD utilized: ₹0.
- Secure concentration: 41.5% (₹287.24L Secure / ₹692.44L total active pipeline — 28 Apr Bigin pull, 96 deals). Still above 25% ceiling. Was 52.5% in CLAUDE.md — updated.
- Bigin pipeline: 96 deals (was 90 on 22 Apr). 8 Closed Won, 17 Existing Confirmed, 8 Design, 2 Price Quote, 22 New Leads, 8 BBANNTI Qualified, 27 Not Qualified, 1 Closed Lost.
- 7 drift ALERTs: closed-won FY27 deals not in Sonal's Projects sheet: Carl Bechem (56 biz days), Mosil IDMC (31), Secure RenewX (25), Messung SHE26 (19), Labguard Anacon26 (19), Amaara Vitafoods (19), GIC ELAsia (14). Sonal flagged via Telegram.
- Labguard Anacon26 (22–24 Apr): T22 ✓ + T23 ✓ — FULLY WRAPPED. Post-show invoicing pending.
- Secure RenewX (27 Apr): T20 ✓, T21 ✓, T22 ✓, T23 ✗ — installation complete, dismantling pics pending.
- Messung SHE26 (28–30 Apr): T21 ✓ — installation started. Show ONGOING today. T22 pending.
- Secure Utility Week Birmingham (19 May): T01 ✓, T02 ✓ — advance received. T03–T06 to set up in Notion (CK).
- Mosil IDMC26 (ended 23 Apr): T20 ✗, T21 ✗, T22 ✗, T23 ✗ — 5 days post-show, unresolved. Dhruv has not updated.
- GIC ELAsia (14–17 May): T02 ✗ — advance still not received. Show in 16 days.
- HDFC 0247/0241 alerts: STILL NOT ENABLED — 3rd session flagged. Zero business bank data in dashboard.
- Production tracker last pulled: 27 Apr 2026 (28 Apr session).

## Verified facts (24 Apr 2026)
- Operating cash: ₹35,86,209 (Sonal, 24 Apr, "Live Data", account 0247). BELOW ₹76.5L floor. Cash breach active. Treasury: ₹1,39,97,249. OD limit: ₹1,21,00,000, OD utilized: ₹0.
- HDFC parser: now filters to ALLOWED_ACCOUNTS {"0247","0241"} only. 63 personal-account transactions filtered out. Zero business transactions in current cache — HDFC alerts for both accounts not yet enabled in NetBanking.
- Receivables hit detection spec saved to memory (pending_hdfc_receivables_check.md): build _validate_bank_vs_sheet() in build_cashflow_json.py once 0247 alerts are live.
- Secure RenewX 27 Apr: T07–T18 ALL ticked (24 Apr). Last milestone: T18 Graphics Check. Show in 3 days. T20/T21 on-site pending.
- GIC ELAsia: T03 Costing Drawing ✓ (24 Apr). T02 advance still NOT received. Show 14–17 May.
- Messung SHE26: T13 ✓ + T18 ✓ (24 Apr). T22 Handover Pics already ✓. Show 28–30 Apr.
- Labguard Anacon26: T18 ✓ (24 Apr). T22 still ✗ — show last day today (24 Apr). T22/T23 pics needed today.
- Mosil IDMC26: Show ENDED (23–24 Apr). T21 still ✗. Chase Dhruv for T21/T22/T23 urgently.
- Utility Week Birmingham ₹47.95L: in active-projects.md + bigin_pipeline_raw.json. Drift: INFO (recently closed, awaiting Sonal Projects sheet row). Will escalate to ALERT next /finance if not added.
- EM Power Munich: amount confirmed ₹32.0L (was TBC). Requirement gathering. Closing 5 May.
- Production tracker last pulled: 24 Apr 2026.

## Verified facts (23 Apr 2026)
- FirstRain-Cashflow-Master 7-tab audit complete. Dead columns deleted. Invoices_Raised tab deleted. Bigin_Deal_ID removed from Projects. Vendor outflow now auto-computed from Projects CP. CONFIG_MONTHLY_BURN_YYYY-MM pattern live in Notes parser.
- /close skill 0C: no longer fetches CSV. Reads data/projects/sheet_cash_position.json from last /finance run.
- Secure Utility Week CLOSED WON 22 Apr: ₹47.95L (CK). Was Design at ₹22.46L. Show 19 May NEC Birmingham. Notion column exists. T01-T06 milestones to set up.
- Messung SHE26: T22 Handover Pics ✓ (22 Apr). Stall delivered ahead of 28-30 Apr show.
- Labguard Anacon26: T21 ✓, T22 ✗ — show Day 2 of 3 (ends today 23 Apr).
- Mosil IDMC26: Show TODAY (23 Apr). T21 status unknown — Dhruv to confirm.
- Cash_Position tab showing Rs61,526 (wrong — likely Sonal hasn't populated new tab post-restructure). Do not use. Last known operating cash Rs11,54,623 (21 Apr).
- Code commit 62d6a91: drift_check.py soft-match only; build_cashflow_json.py vendor outflow from Projects; read_cashflow_xlsx.py 7 tabs (was 8).

## Verified facts (22 Apr 2026)
- CFO OS Dashboard v3 live: Cash Flow tab shows ₹3.64Cr FY27 inPipeline (Apr 2026–Mar 2027 only). Projects/Alerts/Data tabs all fixed and matching demo. Committed 1fad572.
- claude_bigin_client.py created: Zoho REST OAuth client. Reads BIGIN_CLIENT_ID, BIGIN_CLIENT_SECRET, BIGIN_REFRESH_TOKEN from .env. build_cashflow_json.py calls live Bigin on every render — falls back to cache if .env absent. .env.example at repo root with setup instructions.
- Bigin pipeline (22 Apr): 90 deals in Sales Pipeline 26-27. 8 Closed Won FY27, 18 Existing Confirmed, 9 Design/Quote active.
- New Bigin deal spotted: CK - 40sqm EM Power Munich Germany (Req gathering, Secure Meters, close 5 May) — qualify next session.
- Housing'26 Manchester (₹63.17L) + Installer'26 Birmingham (₹39.31L), both Secure Meters, closing dates were 23 Apr — still in Design as of 22 Apr. CK to advise.
- Labguard Analytica India: ON SITE today (Day 1 of 22–24 Apr). T21 ✓.
- Mosil IDMC Lucknow: Show TOMORROW (23 Apr). T21 NOT ticked. Chase Dhruv urgently.
- Sonal finance sheet CSV URL returning 404 — publish link expired. Sonal needs to re-publish from Google Sheets.
- Notion production tracker row-level data: 404 on view fetch — production status held at 21 Apr 2026.

## Verified outbound facts [added 11 Jun 2026]
- Bauma CONEXPO India 2026: 28 Sep–1 Oct, India Expo Centre Greater Noida (Bigin deal names confirm venue; Intel wiki "BIEC Bengaluru" was wrong inference). Mosil 18sqm ₹3.78L Existing Confirmed; Molygraph 39sqm ₹5.95L Closed Won at 2024 edition. Contact both: Dennis Mathew.
- Bauma shortlist (Niloy, 10 accounts): JCB, SCHWING Stetter, Escorts Kubota, Tata Hitachi, Volvo CE, Liebherr, ACE, SANY, Doosan Bobcat, Putzmeister. NONE in Bigin. JCB/Liebherr/Putzmeister NOT in 2024 exhibitor scrape — verify 2026 participation.
- Confirmed still in seat (Niloy, 11 Jun): Tarun Singhal = Chief Marketing Manager ACE (tarun.singhal@ace-cranes.com, +91 9560144199); Baskar Babu @ SCHWING Stetter (baskarbabu.s@schwingstetterindia.com); P Sathya @ Caterpillar (sathya_p@cat.com). Reconnect sequences drafted for all 3 in _outputs/.
- Unworked warm leads from 2019 Gmail thread: Abhishek Phadnis (Hyundai CE Marcom Mgr, abhishek.phadnis@hyundaiindia.net, 9607984373 — internal referral); Apsara Bandopadhyay (Volvo CE — replied "keep in mind"); Rajan Arya (SANY — phone call happened).
- RR Kabel (= RR Global): LIVE Bigin deal "ND - Deal for Rajesh Jain", New Leads & Enquiries, Smarter E Europe context — NOT a cold ABM target.
- Utkarsh India: 3 Bigin deals all Not Qualified (Feb 2026), contact Anindya Sarkar via referral — re-engage, not cold.
- No Bauma 2024 outdoor case study exists. Molygraph 2024 build was indoor hall. Never claim outdoor case studies in outreach.

## Verified facts (16 Jun 2026)
- HDFC parser handles three credit alert templates: P_CREDIT (legacy "View: Account update" subject), P_NEW_DEPOSIT_ALERT (new "❗ New Deposit Alert" subject — recovered ~₹2.82Cr of 30d credits previously dropped), and the cheque-deposit / FCY-inward variants. _FB_ACCT_RE generic fallback accepts "Account: XX0247" with colon.
- Gmail filter rule "Finance/HDFC-Txn" now also labels "New Deposit Alert" subjects. All 3 sync SKILLs use sender-only query `from:alerts@hdfcbank.bank.in` (no label restriction) so future template variants flow without filter edits.
- Statutory tab schema is now `Statutory-1` (44 rows: 12 GSTR-3B + 12 GSTR-1 + 4 TDS-24Q + 4 TDS-26Q + 12 PT-MH). Legacy `Statutory` retained as fallback. Parser reads either via the `_load_tab(wb, ["Statutory-1", "Statutory"])` lookup + camelCase→snake_case header normalisation. Ravindra owns projected `amountPayable` updates.
- Revenue projection model: 75% advance at Bigin close month + 25% balance close month + 1 (net-30). Vendor cost stays anchored to close month (work month), not the trailing 25% cash month.
- Treasury Sweep deployable surplus = `min(today_surplus, horizon_surplus)`. Surplus from uncollected receivables is shown as `HOLD_PENDING_COLLECTION` direction, never recommended for deployment.
- HDFC bank balance reconciliation: `_reconcile_bank_balance()` compares computed running total vs email-embedded "Available Balance" line. Status: ok < ₹10K, drift < ₹1L, material_gap > ₹1L. Dashboard badge surfaces it; heal-check Step 4B alerts via Telegram.
- Dashboard deploy rule: ALWAYS `bash scripts/deploy_dashboard.sh`. Raw `wrangler pages deploy` defaults to Preview environment — causes silent Production-stale regressions. Script's Layer 4b guard asserts Production post-deploy.
- Days-overdue uses `expected_date` if later than `due_date` — Secure UW Birmingham 17d (not 50d).
- Show_Project column now on both Receivables and Payables tabs; rendered inline on Collect and Pay dashboard tabs between invoice no and exec/approver.
- Secure UW Birmingham received ₹13.70L RTGS today (16 Jun), most of ₹14.69L balance. ~₹99K residual pending. Sonal to mark partial-paid.
- Housing'26 Manchester (₹122L) + Installer'26 Birmingham (₹93.79L) Closed Won 20 May — DOTTS Expo (Poland) fabricator. NOT yet in Sonal's Projects sheet, so dashboard YTD synthesises from Bigin Won by company-name + show-prefix dedup.
