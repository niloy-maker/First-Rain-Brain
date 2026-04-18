---
name: intel-query
description: Self-serve wiki search for Pankaj and Dhruv. Answers questions about shows, companies, and sectors using only FirstRain-Intel wiki content. Read-only. Never uses general knowledge.
triggers: ["/intel-query", "ask the wiki", "what does the wiki say about"]
---

# /intel-query — Intel Wiki Search

This skill is for Pankaj and Dhruv. It answers questions about shows, companies, and sectors using only what is already in the FirstRain-Intel wiki. It never makes things up.

---

## Step 1 — Read the question

The question will be in plain language after `/intel-query`. Examples:
- `/intel-query Which pharma shows in June are High priority?`
- `/intel-query What do we know about IPCA Laboratories?`
- `/intel-query Who are the competitors we've profiled?`
- `/intel-query Which shows in July have leads identified?`

If no question is provided, ask: "What would you like to know? Ask me anything about shows, companies, or sectors in the Intel wiki."

If the question involves pricing, margins, or financial rules → stop and say:
"That involves pricing rules — check with Niloy directly."

---

## Step 2 — Read index.md first

Read `FirstRain-Intel/index.md`.

Use it to identify which pages are most relevant to the question. Do not read every page — only the ones that match.

Routing rules:
- Question about a company or prospect → look for it in Accounts sections → read `FirstRain-Intel/wiki/accounts/{slug}.md`
- Question about a show → look for it in Shows sections → read `FirstRain-Intel/wiki/shows/{slug}.md`
- Question about a sector → read `FirstRain-Intel/wiki/sectors/{slug}.md`
- Question about a competitor → read `FirstRain-Intel/wiki/competitors/{slug}.md`
- Broad question (e.g. "which shows in June are High priority?") → read index.md and extract the answer directly from the tables — only read individual show pages if you need more detail than the index provides

---

## Step 3 — Read the relevant pages

Read only the pages identified in Step 2. Maximum 5 pages per query unless the question explicitly asks for a broad list.

If a page does not exist for the topic asked → do not guess. Proceed to Step 4 with what you have.

---

## Step 4 — Synthesise the answer

Rules — follow these exactly:
- **Only use information from the wiki pages you read.** Never use general knowledge about companies, shows, or industries.
- If the wiki does not have an answer → say exactly: "The Intel wiki doesn't have this yet. Clip a source into `FirstRain-Intel/raw/` using the Web Clipper and ask Niloy to ingest it."
- Always cite which wiki page(s) the answer came from.
- Keep answers under 200 words unless the question asks for a full list.
- Use plain language. Pankaj and Dhruv are not Claude Code users — write for a business reader.

---

## Step 5 — Output the answer

Format every answer like this:

```
---
INTEL QUERY — [question]
Date: [today's date]

[Answer in plain language — from wiki pages only]

Source: FirstRain-Intel wiki — [list the pages read, e.g. wiki/shows/cphi-mea.md, wiki/accounts/ipca-laboratories.md]
---
```

---

## Step 6 — Save the output

Save to: `_outputs/intel-query-[YYYY-MM-DD]-[2-3 word topic].md`

Tell the user the answer inline (don't make them open the file). The save is just for the record.

---

## Hard rules

- **NEVER update, edit, or write to any wiki page during a query.** Query = read only.
- **NEVER make up information.** If it's not in the wiki, say so.
- **NEVER use Claude's general knowledge** about companies, industries, or shows. Wiki only.
- If asked something that touches financial rules, margins, or pricing → say "Check with Niloy directly."
