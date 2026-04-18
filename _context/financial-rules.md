# First Rain — Financial Rules
# Single source of truth. Load when: quotes, margins, cash, receivables.
# Last updated: April 2026. Update after every bank statement.

## Margin floors (hard floor — no exceptions)
- India projects: 33% contribution margin minimum
- International projects: 38% minimum
- Formula: CM% = (SP − CP) / SP × 100

## Monthly burn
- FY26-27 projected: ₹25,50,000/month | Annual: ₹3,06,00,000
- FY25-26 actual: ₹23,00,000/month (reference only)

## Alert thresholds
- MARGIN ALERT: Any quote below 33%
- CONCENTRATION ALERT: Secure Meters above 25% (currently 52.5% — live breach)
- RUNWAY ALERT: Operating cash below ₹76,50,000 (3 months at ₹25.5L)

## Current cash position (update weekly)
**Source: Sonal's Weekly Finance Report — Google Drive → FirstRain-Weekly-Reports/Finance**
**Template: _outputs/Sonal-Weekly-Finance-Report-Template.xlsx**
**Cadence: Sonal uploads every Monday by 10am. Claude reads before /monday.**

- Operating cash: ₹24,56,438 — CRITICAL (1.0 months) [last updated: 18 Apr 2026 — Sonal's sheet]
- Treasury: ₹1,39,97,287 — real buffer
- OD Facility: ₹1,21,00,000
- Total receivables: ₹26,70,705

## Receivables priority (update weekly — from Sonal's report)
| Client          | Amount       | Status                          |
|-----------------|-------------|----------------------------------|
| Amaara Vitafoods | ₹14,00,000 | #1 — ₹20L received 14 Apr. ₹14L outstanding. Chase before 5 May (90% rule). |
| Messung         | ₹4,63,905   | #2 — April. Show 28-30 Apr.     |
| Elliott Ebara   | ₹93,800     | #3 — Small residual per Sonal's sheet (daily-updates shows cleared 14 Apr — verify with Sonal) |
| Secure BES      | ₹6,50,000   | #4 — ₹6.5L outstanding per Sonal's sheet (18 Apr). Source of truth. |
| Mosil           | ₹63,000     | #5 — April. Show 23 Apr.        |
| Carl Bechem     | ₹0          | ₹1,16,800 received 15 Apr ✓ (NEFT AXISP00788721946). BME Conclave wrap pending (T23–T31). |

## Quote checklist (all 4 must pass)
1. SP − CP above 33% of SP?
2. Secure Meters still below 25% of annual revenue?
3. Client account above ₹15L for this FY?
4. Fabrication cost risk in new geography?
4/4 pass → Proceed | Any fail → Flag and reprice

## Permanent client pricing rules
| Client        | Rule                                                    |
|---------------|----------------------------------------------------------|
| Elliott Ebara | PO required before Closed Won. Verbal ≠ revenue. Always.|
| Gerresheimer  | 71% margin FY26. Never discount. Protect always.        |
| Amaara        | Blended 33% across ALL FY27 shows. Flag below 33%.      |
| Nordex        | Floor ₹21.14L SP. CP max ₹15.91L. Hold firm.           |
| Klenzaids     | Hold firm. Scope reduction only lever. No price cuts.   |

## Active strategic exception
Amaara Vitafoods Europe May 2026: CM 17.6% (SP ₹34L, CP ₹28L)
Rationale: margin recovery committed across future Amaara shows.
Flag immediately if any subsequent Amaara quote comes in below 33%.

## FY25-26 verified actuals
- Total Revenue: ₹6,84,22,552 | Total Contribution: ₹2,67,95,377
- Blended CM%: 40.4% (NOT 51% — earlier estimate was an error)
- FY26 closed at deficit ~₹8L against ₹2.76 Cr annual burn

## ZOHO vs TALLY — CRITICAL SYSTEM NOTE
**Zoho Books is used for Quotation / Estimation / Proposal only.**
**Actual invoicing happens in Tally. Tally is the financial source of truth.**

Implications:
- Never use Zoho invoice totals for revenue or receivables reporting — use Tally
- All "draft" invoices in Zoho are proposals/estimates, not actual invoices
- Zoho outstanding balances ≠ actual AR — always cross-check with Tally / Sonal
- agent-finance must pull actuals from Sonal / Tally, not from Zoho invoice API
- Scatterpie Analytics ₹23,36,400 in Zoho = rental income, not exhibition revenue — Tally handles separately

## Non-exhibition revenue (exclude from CM% and client scorecard)
- Scatterpie Analytics — TENANT. Monthly rent ₹2,12,400. Not a client. Handle via Tally / Sonal only.

## FY26-27 pipeline status
- Confirmed pipeline SP: ₹3.92 Cr
- At 40.4% CM: contribution ~₹1.58 Cr vs ₹3.06 Cr burn = ₹1.48 Cr deficit
- Secure Meters: 52.5% of pipeline — DOUBLE breach of 25% ceiling

## Bigin pipeline sync — SINGLE SOURCE OF TRUTH for FY26-27 revenue
**Sub-Pipeline: "Sales Pipeline 26-27" | 9 stages only**
**Check Bigin before every /monday and /production. Last pulled: 11 Apr 2026.**
**Note: Sub_Pipeline filter not supported in COQL — filter by the 4 unique stages + deal name prefix (CK-/DS-/SP-/ND-) to isolate 26-27 records.**

### Stage 1 — Closed Won 26-27 (6 deals | ₹66.57L confirmed SP)
| Deal | Client | SP | Show Date |
|------|--------|----|-----------|
| Vitafoods Europe | Amaara | ₹34.0L | ~5 May 2026 |
| Analytica Lab India | Labguard | ₹13.6L | 22–24 Apr 2026 |
| Smart Home Expo JWCC | Messung | ₹6.3L | 28–30 Apr 2026 |
| RenewX'26 Chennai | Secure Meters | ₹9.35L | Mar 2026 ✓ |
| BME Conclave 2026 | Carl Bechem | ₹1.82L | 8–9 Apr 2026 ✓ |
| IDMC Lucknow | Mosil | ₹1.5L | 23–24 Apr 2026 |

### Stage 2 — Existing Confirmed (17 deals | ₹2.35 Cr pipeline)
| Client | Key Shows | SP |
|--------|-----------|----|
| Christie Digital | Infocomm'26 (₹41.17L) + BigCineExpo'26 (₹14.4L) | ₹55.57L |
| Amaara | Supply Side Global (₹38.21L) + Bangkok (₹16.28L) | ₹54.49L |
| Elliott Ebara | IEW'27 Goa | ₹30.7L |
| Carl Bechem | IMTEX'27+Wire India+ITME+Pune (4 shows) | ₹26.64L |
| Iberchem | Cosmohome'26 (₹18L) + HPCI'27 (₹7L) | ₹25.0L |
| Swarn Shilp | DJGF'26 Pragati Maidan | ₹11.0L |
| Mosil | UBEiNX + Bauma'26 | ₹11.13L |
| Molygraph | UBEiNX New Delhi | ₹6.3L |
| Spectrum Filtration | Pmec India'26 | ₹6.12L |
| Enzyme Bioscience | Vitafoods'27 JWCC | ₹7.78L |

### Stage 3 — Design (10 deals | ~₹2.42 Cr — Secure heavy)
| Deal | Client | SP | Closing Date |
|------|---------|----|-------------|
| 81sqm Enlit Europe'26, Vienna | Secure Meters | ₹76.95L | 10 Aug 2026 |
| 67.5sqm Housing'26, Manchester | Secure Meters | ₹63.17L | 23 Apr 2026 |
| 42sqm Installer'26, Birmingham | Secure Meters | ₹39.31L | 23 Apr 2026 |
| 24sqm Utility Week'26, Birmingham | Secure Meters | ₹22.46L | 26 Mar 2026 |
| 130sqm Windergy'26, Chennai | Nordex Energy | ₹23.46L | 16 Jul 2026 |
| 60sqm Pharma Pro & Pack | Klenzaids | ₹10.0L | 21 May 2026 |
| 36sqm ELAsia BIEC | GIC | ₹7.2L | — |
| ⚠️ Duplicate/old records for Installer'26 + Housing'26 — verify with Chinmay | | | |

### Stage 4 — Price Quote (2 deals | ₹27.4L)
| Deal | Client | SP | Closing Date |
|------|---------|----|-------------|
| 30sqm MEE'26 Dubai | Secure Meters | ₹18.5L | 23 Jul 2026 |
| 56sqm Pharma Pro & Pack | ZETA GmbH | ₹8.9L | — |

### Stage 5 — BBANNTI Qualified (6 deals | amounts TBC)
| Deal | Client | Closing Date |
|------|--------|-------------|
| EPR Vietnam (Ho Chi Minh) | Secure Meters | 20 Aug 2026 |
| EPR Indonesia / Enlit Asia | Secure Meters | 16 Jul 2026 |
| African Energy Week, Cape Town | Secure Meters | 13 Aug 2026 |
| CIGRE, Paris | Secure Meters | 14 May 2026 |
| Elecrama 2027, Greater Noida | Secure Meters | 1 Dec 2026 |
| Bharat Mobility Show'27 | Carl Bechem | 7 Dec 2026 |

### Stage 6 — New Leads & Enquiries (13 deals | no amounts)
Klenzaids (Pmec'26), Christie Digital duplicates, Anish Pharma (×2), Truetzschler, ATE Enterprises, Axis Electricals, Platinum Industries, SBEE Cables, Snowbell, Moleculez, PCM Railone, Disha Foods, protectt.ai

### Stage 7 — Requirement Gathering (3 deals)
Amaara Vitafoods Europe ₹22.95L (older version — superseded by Closed Won), Amaara Vitafoods Asia (no amount), Electro Crimp/IEEE Chicago (no amount)

### Stage 8 — Not Qualified | Stage 9 — Closed Lost
200+ old records from 2022–2025 Sales Pipeline — ignore for FY27 planning.

### Secure Meters concentration in 26-27 pipeline (live breach)
| Stage | SP |
|-------|----|
| Closed Won 26-27 | ₹9.35L |
| Design | ~₹2.02 Cr (4 confirmed shows) |
| Price Quote | ₹18.5L |
| BBANNTI Qualified | TBC (5 shows) |
| **Total Secure in pipeline** | **~₹2.49 Cr** |
**Concentration alert: Secure is ~43% of all deals with known amounts. 25% ceiling = live breach.**
