# CLAUDE.md — FirstRain-Intel Wiki Instructions

## About First Rain

**First Rain Exhibits India Pvt. Ltd.** is a 20-year-old exhibition stand design and build company. This wiki is the company's internal market intelligence system — a living knowledge base about the trade show ecosystem in which First Rain operates and sells.

---

## ICP, Priority Sectors and Disqualifiers
Load `../_context/icp-rules.md` — do not duplicate here.
That file is the single source of truth. Use it to:
- Qualify or disqualify any company before writing an intel article
- Confirm sector priority when tagging articles
- Apply BBANTI framework when evaluating show exhibitor lists

## Priority Shows
Load `../_context/lead-gen-system.md` for the full show calendar.
The Intel wiki covers shows that are in scope per that file.
When in doubt about whether a show is worth tracking: check if it appears in lead-gen-system.md first.

---

## Wiki Structure

```
FirstRain-Intel/
├── raw/              ← Drop source documents here (PDFs, URLs, notes, screenshots)
├── wiki/
│   ├── sectors/      ← One article per sector (e.g., pharma.md, hvac.md)
│   ├── shows/        ← One article per trade show (e.g., cphi-india.md)
│   ├── fabricators/  ← Intel on stand fabricators / competitors
│   ├── accounts/     ← Intel on specific target companies / clients
│   └── competitors/  ← Intel on competing stand design & build firms
├── index.md          ← Master list of all wiki articles (kept up to date)
├── log.md            ← Ingest history (date + source + what was added)
└── CLAUDE.md         ← This file
```

---

## Ingest Protocol

When a source document is dropped into `raw/` or provided directly, follow these steps:

### 1. Tag every source with
- `sector:` — which priority sector does this relate to?
- `show:` — which trade show(s) are mentioned or relevant?
- `geography:` — India domestic / international / global?
- `company:` — which company/companies are named?

### 2. Write or update the relevant wiki article(s)
- Place sector intel in `wiki/sectors/<sector-name>.md`
- Place show intel in `wiki/shows/<show-name>.md`
- Place company intel in `wiki/accounts/<company-name>.md`
- Place competitor intel in `wiki/competitors/<competitor-name>.md`

### 3. Update `index.md`
- Add a new row to the relevant section table
- Include: article name, sector tags, show tags, date last updated

### 4. Log the ingest in `log.md`
- Format: `YYYY-MM-DD | <source name> | <what was added/updated>`

---

## Article Format (Wiki Pages)

Each wiki article should follow this structure:

```markdown
---
tags: [sector/<name>, show/<name>, geography/india]
last_updated: YYYY-MM-DD
---

# <Article Title>

## Summary
One paragraph overview.

## Key Facts
- Bullet points of the most important intel

## Exhibitor / Company Details
(if account or show article)

## Notes & Observations
Qualitative intel, patterns, opportunities

## Sources
- Source name — YYYY-MM-DD
```

---

## Rules

- Never delete content from `log.md` — it is append-only.
- Always update `index.md` after every ingest — it must stay current.
- If a wiki article already exists for a company or topic, **update it** rather than creating a duplicate.
- Keep articles factual and concise. Flag speculation clearly with `[inference]`.
- If a source is ambiguous about sector, tag all plausible sectors.
