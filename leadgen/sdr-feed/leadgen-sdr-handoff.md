# leadgen-sdr-handoff

> **Purpose:** Session handoff from Claude chat → Claude Code. Everything a fresh session
> needs to continue the 2-SDR international feed build without re-litigating settled strategy.
> **Date:** 13 July 2026
> **Status:** Strategy settled. Feed engine built. Awaiting Q3 target shows + exhibitor lists.

---

## 1. WHAT WAS DECIDED (do not reopen)

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Both SDRs hunt international, bidirectionally.** SDR 1 = inbound (foreign companies exhibiting *in* India). SDR 2 = outbound (Indian companies exhibiting *internationally*). | Inbound = best margin (build in India, VAT-clean, design+PM moat at full strength) and is current white space. Outbound = scales the proven motion (Enlit / SMM / Supplyside / Sibos). |
| D2 | **Domestic India stays PE-farmed (Dhruv). NOT an SDR hunting target.** | Lowest margin, most price-competitive. Needs farming, not hunting. |
| D3 | **UK is PARKED — all three routes.** Agency white-label, direct-to-UK-exhibitor, and UK entity + ESSA. | See §2. Not killed — deferred, with named trigger conditions. |
| D4 | **Concentration mandate overrides both SDRs.** Named share of monthly new pipeline must come from outside Secure Meters and outside energy-only. | Structural risk: Secure Meters over-concentration in CK's book; CK is a succession risk (MBA departure). |
| D5 | **Pillar sequence:** Energy (G1, existing) → **Pharma (G4, second pillar)** → Specialty Chemicals (G5, third). | 25 CPhI accounts already seeded in Notion — activate into ABM Group 4. |
| D6 | **250 connects/week/SDR is a TOUCH number, not a net-new-account number.** Resolved via T1/T2 tiering. | A narrow custom-build ICP does not contain 1,000 fresh qualified accounts/SDR/month. Forcing it = spray. See §4. |
| D7 | **No fabricated contacts, ever.** Every row traces to a real published source URL. | Invented contacts burn SDR credibility and brand. Non-negotiable. |

---

## 2. UK — WHY PARKED, AND THE TRIGGERS TO REVISIT

Three separate routes were evaluated. All deferred. **They partly conflict with each other** —
that conflict is the reason to sequence, not to pick blind.

**Route A — White-label for UK agencies (production backend).**
- Right *business*, wrong *first job for an SDR*. Agency selling = few targets (5–10), sophisticated
  buyers who know fabrication cost cold, founder/senior-BD relationship sale. Not SDR-shaped.
- **Blocker:** Dotts (Poland) not yet Doha-approved. Poland fabrication is the cost engine of the
  entire pitch — cannot sell margin math on an unvetted vendor.
- **Blocker:** UK VAT/invoicing structure undefined.
- Caveat: rents out the moat (agency keeps design + client). Beachhead only, never the destination.

**Route B — Direct to UK exhibitors.**
- **Channel conflict:** cannot be the invisible white-label backend for UK agencies AND compete with
  them for the same end clients. Irreconcilable without hard segmentation that is difficult to police.
- **No moat:** fresh Ltd, one reference, facing GH Display / Team Tecna / Icon — who are currently
  *fabrication partners*. Only wedge would be "India design + Poland fab = cheaper" → the exact
  commodity trap the whole positioning exists to escape.

**Route C — UK entity + ESSA.**
- The real lever is **VAT**, not targeting. A UK VAT-registered entity kills the non-recoverable
  UK VAT asymmetry (6–12 month lag) — a structural margin gain on *every* UK motion.
- Cost: deliberate UK permanent establishment → UK corp tax, Companies House, VAT returns,
  transfer pricing (India parent ↔ UK sub), realistically a UK-resident operator.
- ESSA: plain membership = modest badge. **ESSA *Accredited*** = audited H&S, maps to CDM 2015,
  increasingly required by venues/organisers. Requires £5m Public Liability, credit/financial checks,
  peer review. **Only earns its keep if First Rain is the principal contractor physically building** —
  if white-labelling behind an agency or building through accredited UK fabricators, *they* carry it
  and ours is decorative.

**Trigger to revisit:** UK build volume × VAT leakage exceeds entity running cost. (Secure Meters
book ~₹1.5 Cr across three builds may already be enough — run the numbers before reopening.)

**Also established (Motion B sizing):** Indian companies taking *custom* UK stands ≈ **20–50/year**,
not hundreds. Most Indian overseas exhibitors go via EPC "India Pavilion" shell schemes (not ICP).
The UK also lacks the giant sector magnets India has, and CPhI Worldwide — the biggest vein of large
Indian pharma custom stands — rotates around continental Europe, not the UK. **Too thin for a
dedicated SDR.** Treat as bidirectional upside on accounts already worked, not a standalone list.

---

## 3. FILES (place in vault)

```
~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain/
  leadgen/sdr-feed/
    leadgen-sdr-feed-system.md        # the engine: tiering, sources, filters, schema, gates
    leadgen-sdr1-inbound-seed.csv     # 42 anchor accounts (foreign majors → Indian shows)
    leadgen-sdr2-outbound-seed.csv    # 42 anchor accounts (Indian majors → intl shows)
    leadgen-sdr-handoff.md            # this file
```

`leadgen-*` prefix avoids `cashflow-*` collision. Pre-BYSS parked material in
`_context/parked/leadgen-pre-byss/` stays untouched.

**BYSS constraint still active:** no dashboard schema changes and no BANNTI custom-field creation
in Bigin until post-BYSS reconciliation (checkpoints Weeks 4/8/12). The feed CSVs use *existing*
Bigin fields only — do not create custom fields to accommodate them.

---

## 4. THE VOLUME RECONCILIATION (the crux — read before touching the list)

Target: ~250 outbound connects/week/SDR → ~1,000/month/SDR → ~2,000 total.

| Tier | Source | Qualification | Contacts/acct | Touch model | Refill |
|------|--------|---------------|---------------|-------------|--------|
| **T1 — ABM core** | Hand-research + existing show book | Full ICP + custom-build + tier score | 2–3 | High-touch, 10–12 steps | Slow (show cycle) |
| **T2 — Directory pull** | Published exhibitor directories | ICP sector + size proxy only | 1–2 | Lighter, 5–6 steps | Every show edition |

**Month-1 per SDR:** ~60–80 T1 accounts (≈180 contacts) + ~700–800 T2 contacts = ~900–1,000. Front-loaded.

**Qualification gate (must pass all three):**
1. Sector ∈ ABM G1–G5 (Energy/Metering, Architecture/Interior, Construction Machinery, Pharma, Specialty Chem)
2. **Custom-build signal:** bare-space / island / ≥18–20 sqm — **NOT a shell-scheme pavilion slot**
3. Size proxy: independent stand budget (revenue tier / prior large-stand history / MNC status)

**Tier score:** +3 ABM priority sector (pharma/chem count double toward concentration mandate);
+2 large/island history; +2 multi-show exhibitor; +1 already in Bigin as lost/dormant;
**−3 pure pavilion/shell-scheme → T2 max or discard.** T1 = ≥6. T2 = 3–5. Discard <3.

---

## 5. CURRENT STATE OF THE SEED FILES

- **84 anchor accounts total** (42 + 42). These are the **T1 spine**, not a full feed.
- Every row: `Exhibiting_Status = VERIFY` — anchors are *plausible* exhibitors, **not confirmed**
  against the current edition's floor. **Must be verified against live directories before use.**
- Every row: `Contact_Status = PENDING` — **no contacts exist yet.** Names/emails/LinkedIn must come
  from Sales Navigator + Apollo/Lusha/Cognism per the SOP in the feed-system file. **Do not invent.**
- Pharma/chem rows pre-flagged `Concentration_Flag = TRUE` (feeds the weekly concentration sub-target).

---

## 6. NEXT ACTIONS (in order)

1. **[Niloy]** Supply **Q3 target shows + exhibitor lists** — this is the live open thread.
   Most useful format: exhibitor lists themselves (CSV/HTML) or directory URLs, stand sizes if
   the source carries them, and an inbound/outbound tag per show.
2. **Verify the 84 anchors** against current exhibitor directories (~½ day).
3. **Run the T2 directory pull** to ~900 rows/SDR (1–2 days; VA or scraper).
4. **Enrich contacts** (Apollo bulk append against the account list). Compliance: B2B only,
   honour opt-outs, India DPDP + EU GDPR legitimate-interest basis.
5. **Load to Bigin** — `Sales Pipeline 26-27`, PE-prefix discipline (CK-/SP-/DS-/ND-).
6. **Proof-of-machine (recommended before scaling):** run the full T2 pull on **ONE** show first —
   **ELECRAMA** (deepest credibility, energy) — to measure real fill rate and contactability
   before committing across all six shows.

---

## 7. TOOL SPLIT — IMPORTANT

Claude Code does **not** carry this project's MCP connections (no Bigin, no Gmail, no web search)
and does not inherit chat memory. Plan accordingly:

- **Claude Code owns:** the vault, the CSVs, filtering/scoring logic, git trail, file writes.
  (Single-writer discipline: Claude Code is the sole writer to vault files.)
- **Claude chat owns:** live directory/web research, Bigin COQL pulls, exhibitor-list fetching.

**Do not migrate the whole workflow to Code expecting parity — you lose the research half.**
Pragmatic sequence for Q3: bring shows + lists into **chat** for directory work and ICP filtering
against live sources → commit the resulting files via **Claude Code**.
If running entirely in Code, exhibitor lists must be downloaded to disk (CSV/HTML) first.

**Bigin COQL pattern (chat side):**
`SELECT ... FROM Pipelines WHERE Pipeline = 'Sales Pipeline 26-27' LIMIT 200` — fetch broad,
then segment by stage and PE prefix. Filter by Account ID, not name string.

---

## 8. STANDING RULES THAT GATE THIS WORK

- **Elliott Ebara rule:** no fabricator PO until client PO confirmed. Non-negotiable.
- **Doha Protocol:** six-item vetting checklist before committing to any new fabricator.
  (Blocks Dotts → blocks the UK agency pitch.)
- **Margin discipline:** 33% CM floor on Secure Meters UK builds; FY26 portfolio average CM as
  benchmark elsewhere.
- **No price-fighting:** SDRs sell design + PM continuity, not sqm rate. Any deal shaping into a
  pure price fight is disqualified, not discounted. This is the guardrail the whole strategy rests on.

---

## 9. 30/60/90 GATES

- **Day 30:** T2 directory pull producing loadable rows at target rate. If a directory proves
  thin/inaccessible → swap the show. **Do not pad with junk.**
- **Day 60:** SDR 1 (inbound) yielding qualified meetings. If not → the inbound directories were
  thinner than assumed; rebalance weight toward SDR 2 / existing book.
- **Day 90:** ≥ target % of *new pipeline value* carries `Concentration_Flag = TRUE`. If Secure
  Meters / energy still dominates, the mandate isn't biting → intervene.

---

## 10. OPEN QUESTIONS FOR NILOY

1. **Is the domestic base genuinely healthy and self-sustaining?** This is the single fact that
   could flip SDR 2 from outbound-international to domestic. Only you have this number. **Check
   before hiring.**
2. What is the **named %** for the concentration mandate (share of monthly new pipeline from
   outside Secure Meters / outside energy)? Currently unset — it needs to be a number, not an aspiration.
3. Hiring sequence: recommend **SDR 1 first**, validate ramp, then SDR 2. Confirm.
