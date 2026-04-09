---
name: icp-qualifier
version: "1.0"
description: >
  Score an inbound lead against First Rain ICP rules. Run whenever a new lead,
  inbound enquiry, prospect, RFQ, cold email reply, LinkedIn DM, website form,
  or referral is mentioned. Output QUALIFIED or DISQUALIFIED with a specific
  reason. If QUALIFIED, propose the Calendly next step.
---

# ICP Qualifier — First Rain

## Reference
Load `_context/icp-rules.md` before scoring. Load `_context/clients.md` only if the
prospect looks like an existing client account.

## Inputs to collect (ask in order, one at a time, wait for answer)
1. Company name
2. Contact name + title
3. Source (website / LinkedIn / referral / show enquiry / email)
4. What did they ask for?
5. Any show or date mentioned?
6. Any budget or stall size mentioned?

If any answer is missing, ask for it before scoring. Do not guess.

## Scoring — run all 6 checks
Check each item against `_context/icp-rules.md`:

1. **Revenue band** — ₹100 Cr+ annual turnover? (infer from company name if unclear, flag uncertainty)
2. **Exhibit frequency** — Do they exhibit 2+ times per year?
3. **Geography** — Gujarat / Mumbai / Delhi NCR / Hyderabad / or international show?
4. **Decision-maker title** — Head of Marketing, VP Marketing, Exhibition Manager, Brand Manager, Corp Comms Director?
5. **Sector fit** — Smart Metering / HVAC / Pharma / Architecture / Industrial / Chemicals / AV / Nutraceuticals / Beauty / Rail / Textile Machinery / Construction Machinery / Stones?
6. **Disqualifiers** — Event agency? Interior designer? Competitor fabricator? Stall under 9 sqm? No show date? No budget range?

## Output format — always exactly this

```
ICP QUALIFIER — [Company]

Contact: [Name, Title]
Source: [Source]
Ask: [One sentence summary]

Checks:
1. Revenue ₹100 Cr+:   [✅ / ❌ / ❓ unknown]
2. Exhibits 2+/year:   [✅ / ❌ / ❓]
3. Geography fit:      [✅ / ❌]
4. DM title fit:       [✅ / ❌]
5. Sector fit:         [✅ / ❌]
6. No disqualifiers:   [✅ / ❌]

Result: [QUALIFIED ✅ / DISQUALIFIED 🔴]
Reason: [one clear sentence]
```

## After QUALIFIED
- Next step: Send Calendly link for a 30-min discovery call with Niloy
- Route to: Dhruv (ABM pipeline) or Chinmay (enterprise)
- Save to: `_outputs/icp-qualified-[company]-[date].md`

## After DISQUALIFIED
- Do NOT send Calendly
- Draft a polite decline using `/ghost` (reference `_context/brand-voice.md`)
- Reason must be specific — name the failed check
- Save to: `_outputs/icp-disqualified-[company]-[date].md`

## Edge cases
- **Unknown revenue** → mark ❓, ask Niloy before qualifying. Never assume ₹100 Cr+.
- **Existing client** → skip ICP, route directly to existing exec (see `_context/team-map.md`)
- **Referral from existing client** → still run all 6 checks but flag "warm lead" in output
- **BBANTI flag** — if brief quality is poor (no show date, no size, no budget), DISQUALIFY for now, ask them to re-submit with details. This is not a permanent rejection.
