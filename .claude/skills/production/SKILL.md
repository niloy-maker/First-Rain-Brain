---
name: production
version: "1.0"
description: Fetch live project task status from Notion for all active projects. Run when Niloy says production, project status, show status, task update, or how are projects going.
---

# Production Command — First Rain V2

## Read first
_context/active-projects.md — for show dates and exec assignments

## Step 1 — Display active projects from context
Show all Closed Won projects from active-projects.md with days to show.

## Step 2 — Fetch live task status from Notion
Notion Projects DB: collection://d62772f4-6bf1-82e3-b83d-077710962b4f
Notion Tasks DB: collection://fe5772f4-6bf1-825a-95f1-07c0e17ebf31

For each project: search Tasks DB by project name.
Retrieve: Task Name, Status, Assigned, Due Date.

## Task status legend
✅ Done · 🔵 In Progress · 🟠 On Hold · 🟣 To Review · ⬜ Not Started · ❌ Cancelled

## Step 3 — Display per project
PROJECT: [Client] | [Show] | [Date] | [Venue]
SP: ₹X | Exec: [Name] | Days to show: [N]

| # | Task | Status | Assigned | Due Date |
|---|------|--------|----------|----------|

## Step 4 — Critical path flags
>30 days: Tasks 1–8 should be Done or In Progress
15–30 days: Tasks 1–12 Done, 13–16 In Progress
<15 days: Tasks 1–19 Done, 20+ In Progress
<7 days: Everything to task 20 must be Done — flag URGENT

## Step 5 — Summary footer
PRODUCTION SUMMARY | [Date]
Active projects: [N] | Total SP: ₹[X] | Closest deadline: [Project] in [N] days
Open flags: [N critical]
