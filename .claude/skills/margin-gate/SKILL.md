---
name: margin-gate
version: "1.0"
description: Run whenever a quote, SP, CP, pricing, discount request, contribution margin, 33% floor, 38% floor, or fabrication cost is mentioned. Calculate margin and output PASS or FAIL before any other response. Mandatory on every quote.
---

# Margin Gate — First Rain V2

## Read first
_context/financial-rules.md

## Calculation
Contribution = SP minus CP
CM% = (SP minus CP) / SP × 100

## Output format — always exactly this
---
MARGIN GATE — [Client] | [Show]
SP: ₹X | CP: ₹X | Contribution: ₹X | CM: X%
Floor: 33% India / 38% International
[PASS ✅ or FAIL 🔴]

If FAIL:
Shortfall: ₹[exact amount]
Minimum SP at current CP: ₹[calculate at floor %]
→ Do not submit this quote. Reprice first.

If Secure Meters (any project):
⚠️ CONCENTRATION: ~52.5% of FY27 pipeline. Ceiling 25%. Live breach.
---

## After FAIL — three alternatives only (never accept the shortfall)
(a) Reduce scope to maintain margin
(b) Offer value-add instead of discount (extended handover, priority scheduling)
(c) Defer to next project where relationship credit applies

## Never
- Suggest accepting below-floor margin
- Skip the concentration alert on any Secure Meters project
- Output anything before the MARGIN GATE block
