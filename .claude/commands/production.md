# /production — First Rain Full Notion Task Breakdown

You are doing a deep production check. Take as many steps as needed.
This command is only run when Niloy specifically wants task-level detail.

## STEP 1 — Load Active Projects
Read P_Projects.md completely.
Note every active project, show date, and days remaining.

## STEP 2 — Fetch Notion Tasks for Each Active Project
Use the Notion workspace:
https://www.notion.so/firstraingroup/26-27-Project-Manager-First-Rain-35b772f46bf1829f956681ec5c16bc13

For each active project:
- Search Tasks DB for all tasks linked to that project
- Fetch: Task Name, Status, Assigned, Due Date
- Group by project

## STEP 3 — Apply Critical Path Rules
- More than 30 days to show → Tasks 1–8 should be Done or In Progress
- 15–30 days to show → Tasks 1–12 Done, 13–16 In Progress
- Less than 15 days to show → Tasks 1–19 Done, 20+ In Progress
- Less than 7 days to show → Everything to task 20 must be Done

## STEP 4 — Output Per Project

For each project output:

PROJECT: [Name] | [Show] | [Date] | [Venue]
Days to show: [N] | Exec: [Name]

| # | Task | Status | Assigned | Due Date |
|---|------|--------|----------|----------|

⚠️ FLAGS
- [Any task behind schedule]
- [Any blank due dates]
- [Any missing fabricator or budget fields]

## STEP 5 — Production Summary Footer

PRODUCTION SUMMARY | FY26-27 | [Date]
Active projects: [N] | Closest deadline: [Project] in [N] days
Open flags: [N] | Tasks with no due date: [N]