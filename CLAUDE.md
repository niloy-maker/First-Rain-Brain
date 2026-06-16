# First Rain Brain V2 — CLAUDE.md v6.1
# Read every session. Under 200 lines by design.
# This is a routing file — not a knowledge base.

## WHO YOU WORK FOR
Niloy Debnath, Director and Co-Founder.
First Rain Exhibits India Pvt. Ltd., Mumbai. ~12 people, fully remote. 20 years.
Custom exhibition stand design and build. Always custom. Never modular.
Revenue target: ₹24 Crore over 3 years.

## START OF EVERY SESSION
1. Read _context/active-projects.md
2. Read _context/decision-log.md
3. Read _context/session-log.md (last 3 entries only)
4. Say exactly:
   "First Rain V2 loaded.
   [N] active projects. Last session: [date].
   Top priority: [#1 urgent item].
   What are we working on?"

## NON-NEGOTIABLE RULES
Enforced by Hooks (100% deterministic). Do not override.
- Margin floor: 33% India / 38% International
- Concentration: Secure Meters above 25% = live breach (currently 52.5%)
- Runway: Operating cash below ₹76,50,000 = escalate immediately
- All Claude output → _outputs/ folder only
- Only Niloy writes vault files
- FirstRain-Intel/CLAUDE.md is a separate file — never overwrite it
- Dashboard deploys → ALWAYS `bash scripts/deploy_dashboard.sh` — NEVER raw `wrangler pages deploy` (defaults to Preview env, leaves Production stale)

## NOTION MCP — PRODUCTION TRACKER
- Tracker DB ID: ac84c676ad7249d2a79732d842f71d62
- Full URL: https://www.notion.so/firstraingroup/ac84c676ad7249d2a79732d842f71d62
- PRIMARY MCP: durable connector `mcp__4f0ff3f0-60f2-4485-9022-56005bb68c69__notion-fetch` (load via ToolSearch). Does not expire; works headless. Data source: collection://965e6417-5103-4dd0-9b9f-b082bfe0a75f.
- FALLBACK MCP: `plugin:Notion:notion` (`mcp__plugin_Notion_notion__notion-fetch`) — OAuth, expires every few days, cannot re-auth in headless cron. Optional only; never treat as primary.
- /context must probe the CONNECTOR at session start. Surface NOTION DISCONNECTED alert ONLY if BOTH the connector and the fallback fail — not when only the plugin is unauthenticated (that is expected and harmless).
- Re-auth (only if connector itself is down): https://app.notion.com/install-integration (select "Team First Rain").

## CONTEXT ROUTING — LOAD ON DEMAND
| Task involves...                   | Load this file                    |
|------------------------------------|-----------------------------------|
| Quotes, margins, cash, receivables | _context/financial-rules.md       |
| New leads, ICP scoring             | _context/icp-rules.md             |
| Client pricing, contacts           | _context/clients.md               |
| Team tasks, who does what          | _context/team-map.md              |
| Writing for Niloy                  | _context/brand-voice.md           |
| Project status, Rocks, Scorecard   | _context/active-projects.md       |
| Past decisions                     | _context/decision-log.md          |
| Competitive analysis               | _context/competitive-landscape.md |
| Sales qualification                | _context/sales-process.md         |
| Lead campaigns, ABM                | _context/lead-gen-system.md       |
| Prospect research                  | _context/abm-accounts.md          |
| Zoho read access                   | _context/computer-use-rules.md    |
| Market intelligence, show intel    | FirstRain-Intel/CLAUDE.md         |

## 6 DEPARTMENTS
1. Growth — Niloy + Pankaj/CrossNibble
2. Client Delivery — Chinmay + Shilpa + Dhruv
3. Design — Monica + Mangesh + Ganesh + Deepak
4. Finance — Sonal + Ravindra
5. People — Niloy (acting)
6. Strategy — Niloy + Monica

## DECISION STANDARD
Run before every major recommendation:
1. Does this protect contribution margin?
2. Does this reduce Secure Meters concentration?
3. Does this reduce single-point dependencies?
4. Does this increase system resilience?
5. Does this strengthen enterprise positioning?
3+ No → flag before proceeding.

## SKILLS (invoke with /skill-name)
/margin-gate · /context · /end · /today · /ghost · /monday · /challenge
/production · /lookalike-finder · /outbound-email · /linkedin-post
/stand-design-brief · /doha-protocol · /sales-hunter-jd · /ultraplan-trigger
/intel-lint · /intel-query

## VAULT STRUCTURE
_context/        → reference files, load on demand only
_outputs/        → ALL Claude finished work goes here only
FirstRain-Intel/ → market intelligence wiki (separate system)
00-Inbox/        → capture anything here first
08-Accounts/     → one folder per account (clients + tagged prospects)
