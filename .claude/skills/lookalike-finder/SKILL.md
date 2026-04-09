---
name: lookalike-finder
version: "1.0"
description: Find ICP-matched prospect accounts. Run when asked to find prospects, who to target, lookalikes, new leads, ABM accounts, or when a show exhibitor list or vertical is mentioned.
---

# Lookalike Finder — First Rain V2

## Read in this order (most to least rich)
1. FirstRain-Intel/index.md — check what account data is already in the wiki
2. FirstRain-Intel/wiki/accounts/ — enriched profiles with confirmed contacts
3. FirstRain-Intel/wiki/shows/ — show-based prospect lists
4. _context/abm-accounts.md — seed list only (fallback if Intel wiki is empty)
5. _context/icp-rules.md — scoring rules

## Seed profiles
| Seed | Sector | Why the seed |
|------|--------|-------------|
| Secure Meters | Energy | Best enterprise relationship |
| Christie Digital | AV/Tech | Highest absolute contribution |
| Gerresheimer | Pharma | Highest margin (71%) |
| Iberchem | Specialty Chemicals | International show experience |

## Three trigger modes
1. "Find lookalikes of [client]" → use that client as seed
2. "Who to target at [show]?" → read Intel wiki/shows/[show] first
3. "Find [sector] prospects" → read Intel wiki/sectors/ + wiki/accounts/

## Output per run (8-12 accounts)
| Company | Sector | Revenue band | Shows they exhibit at | Likely DM title | ICP score | Tier |

## Tiering
- Tier 1 (Niloy manual): confirmed show history, known brand, direct contact available
- Tier 2 (Lemlist + Dhruv): ICP-matched, not yet worked with
- Tier 3 (Nurture only): ICP-fit, no active show signal

## Output
Save to _outputs/lookalikes-[vertical]-[date].md
Flag: send Tier 1+2 to Pankaj for Freckle.io enrichment if not already enriched
