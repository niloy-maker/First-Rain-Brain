# leadgen-sdr-feed-system

> Operating spec for the 2-SDR international feed. Single source of truth for how the
> feed is built, tiered, enriched, and worked. Companion files:
> `leadgen-sdr1-inbound-seed.csv`, `leadgen-sdr2-outbound-seed.csv`.

---

## CONTEXT

Two SDRs, both net-new international hunting. UK is parked. Domestic stays PE-farmed
(Dhruv), not a hunting target.

- **SDR 1 — Inbound:** international companies exhibiting *in* India. Build in India →
  full margin, VAT-clean, design+PM moat at full strength. White space today.
- **SDR 2 — Outbound:** Indian companies exhibiting *internationally*. Scales the proven
  motion (Enlit / SMM / Supplyside / Sibos). Bidirectional UK upside falls out naturally.

**Override mandate (both SDRs):** a named share of new pipeline each month must come from
**outside Secure Meters** and **outside energy-only**. Second pillar = Pharma (Group 4);
third = Specialty Chemicals (Group 5). This is the concentration-break before CK's exit.

---

## THE VOLUME RECONCILIATION (read before touching the list)

Target: ~250 outbound connects/week/SDR → ~1,000/month/SDR → ~2,000 total.

That number is a **touch-volume** number, not a net-new-account number. A narrow custom-build
ICP does NOT contain 1,000 fresh qualified *accounts* per SDR per month. Trying to force it
that way = spraying garbage. Structure instead as two tiers:

| Tier | Source | Qualification | Contacts/acct | Touch model | Refill |
|------|--------|---------------|---------------|-------------|--------|
| **T1 — ABM core** | Hand-research + existing show book | Full ICP + custom-build + tier score | 2–3 | High-touch, 10–12 steps | Slow (show cycle) |
| **T2 — Directory pull** | Published exhibitor directories | ICP sector + size proxy only | 1–2 | Lighter, 5–6 steps | Every show edition |

**Month-1 feed per SDR:** ~60–80 T1 accounts (≈180 contacts) + ~700–800 T2 contacts pulled
from directories = ~900–1,000 contacts. Front-loaded. Supports 250 touches/week with
multi-step sequences. Sustainable because T2 is *directory-refreshed*, never invented.

**Non-negotiable:** every T2 row traces to a real published directory URL. No row exists
that a person can't click back to. This is what keeps the volume honest.

---

## SOURCE REGISTRY (Tier-2 pull targets)

### SDR 1 — Inbound (foreign exhibitors at Indian shows)

| Show | Sector / ABM | Next edition | Venue | Directory URL |
|------|--------------|--------------|-------|---------------|
| ELECRAMA | Energy / T&D / metering (G1) | Feb 2027 | India Expo Mart, Gr. Noida | elecrama.com/exhibitors-list/ ; 10times.com/elecrama-a/exhibitors |
| bauma CONEXPO India | Construction machinery (G3) | Sep 2026 | India Expo Centre, Gr. Noida | bcindia.com ; 10times.com/bc-india/exhibitors |
| CPhI India / PMEC | Pharma + machinery (G4) | Nov 2026 | IICC Yashobhoomi, Delhi | cphi.com (exhibitor directory) |
| electronica India | Electronics/energy (G1) | Sep 2026 | Gr. Noida | electronica-india.com exhibitor directory |
| ACETECH | Architecture / interiors (G2) | Multi-city | BEC Mumbai / Delhi | acetech.in exhibitor list |
| Chemspec India | Specialty chemicals (G5) | Annual | Mumbai | chemspecevents.com/india |

> Inbound targeting note: most foreign majors have an **India subsidiary/marketing team** —
> that is usually the stand decision-maker, not global HQ. Enrich the India entity first.

### SDR 2 — Outbound (Indian exhibitors going abroad)

| Show (destination) | Sector / ABM | Region | Directory URL |
|--------------------|--------------|--------|---------------|
| CPhI Worldwide | Pharma / API (G4) | Europe (Milan/Frankfurt/BCN) | cphi.com exhibitor directory |
| Chemspec Europe / in-cosmetics | Chemicals (G5) | Europe | chemspecevents.com ; in-cosmetics.com |
| Middle East Energy (Dubai) | Energy / electrical (G1) | ME | middleeast-energy.com exhibitor list |
| Enlit Europe / Enlit Asia | Energy (G1) | EU / SEA | enlit-europe.com (existing book) |
| bauma (Munich) / bauma shows | Construction machinery (G3) | EU / ME / SEA | bauma.de exhibitor directory |
| SMM Hamburg, Supplyside, Sibos | Existing pipeline sectors | Global | existing Bigin book |

> Outbound is partly *seeded from your own history* — Enlit/SMM/Supplyside/Sibos exhibitor
> lists you already engaged are the warmest T1 source. Mine Bigin closed-won + closed-lost first.

---

## QUALIFICATION FILTERS

**ICP gate (must pass all):**
1. Sector ∈ {Energy/Metering, Architecture/Interior, Construction Machinery, Pharma, Specialty Chem} (ABM G1–G5)
2. Custom-build signal: takes bare-space / island / ≥18–20 sqm — NOT a shell-scheme pavilion slot
3. Company size proxy: independent stand budget (revenue tier / prior large-stand history / MNC status)

**Tier score (rank within ICP):**
- +3 exhibits in ABM priority sector (pharma/chem count double toward concentration mandate)
- +2 known large/island stand history
- +2 multi-show exhibitor (recurring spend)
- +1 already in Bigin as lost/dormant (warm)
- −3 pure pavilion/shell-scheme participant → drop to T2 max or discard

T1 = score ≥6. T2 = 3–5. Discard <3.

---

## BIGIN IMPORT SCHEMA (feed row → CRM)

Load to `Sales Pipeline 26-27`. PE-prefix discipline on deal names (CK-/SP-/DS-/ND-).

`Account | HQ_Country | ABM_Group | Motion(IN/OUT) | Target_Show | Tier | Stand_Signal |
Concentration_Flag | Source_URL | Contact_Status | Owner_PE | Notes`

- `Concentration_Flag` = TRUE if pharma/chem OR non-Secure-Meters energy → feeds the weekly sub-target.
- `Contact_Status` = PENDING until enriched (see SOP). **Never** ship a row with an invented contact.

---

## CONTACT ENRICHMENT SOP (the piece a data tool must do, not me)

I supply accounts. Contacts (name/title/email/LinkedIn) get enriched legitimately via:
1. **LinkedIn Sales Navigator** — title filters: "Marketing", "Brand", "Events/Exhibitions",
   "Marcomm", "Trade Show", "Demand Gen". Decision-maker for stands ≈ Marketing/Brand head,
   not sales.
2. **Apollo.io / Lusha / Cognism** — bulk email/phone append against the account list.
3. **Show exhibitor directories** — often list a stand contact directly.

Compliance: B2B outreach only; honour opt-outs; India DPDP + EU GDPR legitimate-interest basis;
no scraped personal data outside these consented sources. Keep it clean — this is a brand asset.

---

## WEEKLY CADENCE (how 250 lands)

Per SDR, steady state:
- ~40–50 net-new contacts *entered* into sequence/week (T1 + T2 mix)
- Each contact: 5–6 step multi-channel sequence over ~3 weeks (LI connect → email x3 → LI msg → call)
- 250 touches/week = new entries + follow-ups on in-flight contacts
- Month-1 is front-loaded: load the ~900 pool up front so sequences have fuel from day 3

---

## 30 / 60 / 90 GATES

- **Day 30:** T2 directory pull is producing loadable rows at target rate. If a show directory
  proves thin/inaccessible, swap it — don't pad with junk.
- **Day 60:** SDR 1 inbound yielding qualified meetings. If not, the inbound directories were
  thinner than assumed → rebalance weight toward SDR 2 / existing book.
- **Day 90:** ≥ target % of *new pipeline value* is Concentration_Flag=TRUE. If Secure-Meters/
  energy still dominates, the mandate isn't biting — intervene.

---

## NON-NEGOTIABLES

1. **No fabricated contacts, ever.** Row without a real source URL = deleted, not shipped.
2. **Pavilion/shell-scheme ≠ ICP.** Custom-build signal is a hard gate.
3. **Concentration mandate is a weekly number,** not an aspiration. Tracked in Pankaj's sheet.
4. **Seed accounts are ANCHORS, not verified exhibitors** — every seed row carries
   `Exhibiting_Status = VERIFY` until checked against the current edition directory.
5. **PE-prefix + Bigin logging** from first touch. No shadow lists in spreadsheets.
