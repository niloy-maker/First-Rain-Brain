---
name: stand-design-brief
version: "1.0"
description: Capture a structured stand design brief. Run when a new brief, design brief, client brief, exhibition brief, stall brief, or concept is needed.
---

# Stand Design Brief — First Rain V2

## Read first
- _context/financial-rules.md (margin check on budget)
- _context/clients.md (if existing client)

## Ask in order — one at a time, wait for answer
1. Client name and contact?
2. Show name, date, and venue?
3. Stall size (sqm) and type (island / 3-side / 2-side / inline)?
4. Budget range (indicative SP)?
5. Key message or theme?
6. Must-haves (demo area, meeting room, storage, AV)?
7. Reference stands they like?
8. Brand assets available (logo, colours, guidelines)?
9. Concept needed by when?
10. Who is the final decision-maker?

## After capturing all 10
- Run /margin-gate on the budget range
- Flag if below 33% before any design work starts
- Save brief to _outputs/brief-[client]-[show]-[date].md
- Routing: Komal reviews brief → Mangesh reviews concept (mandatory)
