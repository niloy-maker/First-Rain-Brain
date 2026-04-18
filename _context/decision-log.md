# First Rain — Decision Log
# Curated record of key decisions. Never buried in session-log.
# Updated by /close — only the most important decisions added.
# Claude reads this every session for continuity.

| Date        | Decision                                      | Rationale                        | Owner | Status  |
|-------------|-----------------------------------------------|----------------------------------|-------|---------|
| 18 Apr 2026 | Design team updated in CLAUDE.md — Monica + Mangesh + Ganesh + Deepak (replaces Mangesh + Komal). Strategy now Niloy + Monica. | Komal gone. Monica leading design. Deepak confirmed on interiors. Ganesh added. | Niloy | Done |
| 17 Apr 2026 | Brief Studio (First Rain Design Briefs sheet) wired into daily 9am briefing — Step 2B fetches via curl -L, outputs summary table + synopsis | New process for capturing and reviewing design briefs daily | Niloy | Active |
| 17 Apr 2026 | Finance sheet fetch method changed — WebFetch → curl -L in both monday sync and /close skill | WebFetch could not follow Google Sheets 307 redirect before URL expired; curl -L handles in one call | System | Done |
| 17 Apr 2026 | Inbound BBANTI call script created — B=brief quality, B=₹15L account-level floor, A=correct DM, I=messenger/buyer/skin test | Formalises qualification framework for all inbound enquiries before design time invested | Niloy | Active |
| 15 Apr 2026 | GIC India approved as multi-show target — 3 shows (ELAsia 36sqm, Automation India 46sqm, Elecrama 2027 110sqm), ₹34.83L at 36.8% CM (5% loyalty). EST-26-27-03 created. | New enterprise account, reduces Secure concentration, supports Rock #1 + #2. | Niloy | Active |
| 15 Apr 2026 | /proposal-maker corrected — IGST applied via tax_id on main line item only. Default design option = "Exhibition Stall Design & Build as per submitted design". | EST-26-27-01 format audit revealed wrong two-line-item approach. Fixed in skill + applied to EST-26-27-03. | System | Done |
| 14 Apr 2026 | Telegram delivery: MCP plugin only (@FirstRainOS1_bot). No Python/HTTP API. | Old bot @FirstRainOS_bot inactive. MCP plugin is live channel. | System | Done |
| 14 Apr 2026 | daily-updates.md created as live receivables log. /close + /end prompt for updates. | Briefings were showing stale data — receivables cleared days ago still showing as outstanding. | Niloy | Active |
| 1 Apr 2026  | Labguard Analytica Closed Won ₹13.6L at 47% CM| ICP match, good brief quality    | Niloy | Done    |
| 1 Apr 2026  | Amaara CM 17.6% — strategic exception granted | ₹34L receivable urgency. Blend 33% across FY27 | Niloy | Active |
| 2 Apr 2026  | GH Display selected for Utility Week Birmingham| Quote GH10918/3 £16,319.75. ESSA Tier 5. | Niloy | Active |
| 2 Apr 2026  | Burn rate confirmed ₹25.5L/month FY27        | Sonal verified actuals           | Sonal | Confirmed |
| 8 Apr 2026  | Two sales hunters approved                    | Domestic ₹6-8L base + International ₹7-9L base | Niloy | To hire |
| 13 Apr 2026 | /proposal-maker skill built — Zoho Books integration live | Automates Proforma Invoice creation with T&C, tax, currency | Niloy | Active |
| 8 Apr 2026  | Obsidian vault upgraded to v6.1              | Eliminated duplication. Hooks + _context/ system | Niloy | In Progress |
| 8 Apr 2026  | FirstRain-Intel wiki built on Karpathy pattern| CPhI China 252 contacts ingested | Niloy | Live    |
| 8 Apr 2026  | Vault v6.1 fully operational                 | 14 context files, 15 skills, hooks, 238 show pages, 2 competitor profiles | Niloy | Done |
| 9 Apr 2026  | SOP: Weekly receivables chase cycle created  | Amaara ₹34L backlog exposed the gap. Sonal owns. Runs every Monday. | Sonal | Active |
| 9 Apr 2026  | Zoho Books = proposals/estimation only. Tally = actual invoicing source of truth. | Discovered during FY25-26 client file build. All Zoho "draft" invoices are estimates. | Sonal | Confirmed |
| 9 Apr 2026  | Kelegent Metaplast = same customer as Shree Mahavir Metal (renamed). Two Zoho records to merge. | Found during 08-Accounts build — identical amounts, same dates. | Sonal | To action |
| 9 Apr 2026  | Scatterpie Analytics = tenant, not exhibition client. ₹2,12,400/month rent. Exclude from revenue/CM%. | Confirmed by Niloy during FY25-26 client file review. | Sonal | Confirmed |
| 9 Apr 2026  | Telegram integration live. First Rain Brain accessible via bot. DM policy set to allowlist. | Mobile access to Brain — Niloy can run /context, /end etc. from phone. | Niloy | Done |
| 11 Apr 2026 | 08-Clients renamed to 08-Accounts — clients + tagged prospects in one folder, clearly demarcated. | Needed clear distinction between active clients and prospects receiving estimates. | Niloy | Done |
| 11 Apr 2026 | Chinmay leaving for MBA in ~1 year. Succession plan: redistribute accounts to Shilpa + Dhruv. | Chinmay owns Secure Meters, Christie Digital, Gerresheimer, Bechem — transition planning required now. | Niloy | In Progress |
| 11 Apr 2026 | Brand voice (Exhibitions) now based on StoryBrand BrandScript guide (Jan 2024). Interiors brand voice to be separate document. | Full StoryBrand framework loaded — One-Liner, taglines, BrandScript. Interiors deferred to Q2 FY27. | Niloy | Done |
| 11 Apr 2026 | Bigin "Sales Pipeline 26-27" stage names are exact source of truth in sales-process.md. Klenzaids = prospect, removed from pricing rules. | Pipeline stage definitions now match Bigin exactly. Klenzaids has no Closed Won deal. | Niloy | Done |
| 11 Apr 2026 | Dhruv removed from all campaign responsibilities. Pankaj (CrossNibble) = sole campaign owner. Bigin pipeline management = Niloy only. | Dhruv is PM-focused; campaign work belongs with the agency. Clean ownership. | Niloy | Done |
| 11 Apr 2026 | /schedule skill created: Pankaj report ingest + FirstRain-Intel show analysis (90–120 days) + ICP picks + Telegram + Gmail draft to niloy@firstrain.co.in | Weekly campaign intelligence automated. monday-sync also runs this every Monday. | Niloy | Live |
| 11 Apr 2026 | ABM sector list expanded from 5 to 13 sectors. Groups 1–3 populated (39 accounts). Groups 4–13 pending. | Active client base revealed 8 uncovered sectors. Seed list now reflects actual pipeline. | Niloy | In Progress |
| 13 Apr 2026 | Nanobanana (Gemini Pro Image, 4K) adopted as LinkedIn visual content tool. Whiteboard sketchnote style = standard format. | Quality verified — all elements render correctly (text, highlights, icons, sketches). Default path: _outputs/linkedin-content/images/ | Niloy | Live |
| 13 Apr 2026 | Amaara ₹20L advance received (Vitafoods Europe ₹34L SP). T02 marked ✓ in Notion. Balance ₹14L outstanding. | #1 cash priority partially cleared. Remaining receivable to be chased before show (5 May 2026). | Niloy | Active |
| 13 Apr 2026 | Labguard ₹6,76,200 advance received (Analytica India ₹13.6L SP). ~50% advance. Balance ₹6,83,800 outstanding. Show 22–24 Apr. | T02 ✓. 9 days to show. | Niloy | Active |
| 16 Apr 2026 | IBA (Indian Banks Association) — SIBOS Miami 2026 pitch accepted. 192 sqm, Miami Beach Convention Centre, 28 Sept–1 Oct 2026. First pitch 24 April. Themes: "India: Resilient by Design" / "India: Leading the Fiscal Future". | New enterprise account (Rock #1). International 38% CM floor. Reduces Secure concentration (Rock #2). Chinmay already in email thread with IBA Corp Comms. | Niloy | In Progress |
| 16 Apr 2026 | Daily briefing automation confirmed working — first-rain-monday-sync runs fully unattended 9am IST. Write + Edit permissions added to settings.local.json. No prompts. | Scheduled task was prompting for file write permission during autonomous run — blocking delivery. Fixed. | System | Done |
| 18 Apr 2026 | /intel-lint, /intel-query, and Web Clipper live — FirstRain-Intel wiki now self-serve for Pankaj/Dhruv. Monthly automated health check scheduled (1st of month, 9am IST, CCR). | Intel wiki built 8 Apr needed maintenance tools and self-serve access. All 3 builds from upgrade plan completed and tested. | Niloy | Done |
| 16 Apr 2026 | Carl Bechem ₹1,16,800 received 15 Apr — BME Conclave post-show payment via NEFT. | T27–T31 wrap still pending (T23 dismantling, final invoice, final payment). | Sonal | Active |
