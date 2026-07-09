"""Regression test for the 2026-05-29 → 2026-07-09 GATE 1 milestone blackout.

Root cause: the SKILLs told the LLM to `notion-fetch` the DATABASE id and
expect all row data back. That call returns only the schema (column names,
data source ids) — not per-row __YES__/__NO__ values. The LLM was reading
schema and hallucinating milestone status, then falling back to a 6-week-
stale cache when it noticed the mismatch.

Discovered workaround: notion-search + notion-fetch per row page id. This
test locks the SKILLs to that pattern so no future edit reintroduces the
schema-fetch-as-rows mistake.
"""
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / ".claude" / "scheduled-tasks"
TRACKER_DB_ID = "ac84c676ad7249d2a79732d842f71d62"


class TestGate1UsesSearchAndFetchPerRow(unittest.TestCase):
    """Every SKILL that reads the Production Tracker must use the
    search-then-fetch pattern, not schema-fetch-and-hope."""

    SKILLS_WITH_GATE_1 = [
        "first-rain-monday-sync",
        "first-rain-midday-refresh",
        "first-rain-eod-refresh",
    ]

    def _skill_text(self, name):
        p = SKILL_DIR / name / "SKILL.md"
        if not p.exists():
            self.skipTest(f"SKILL {name} not present in repo copy")
        return p.read_text()

    def test_each_skill_documents_search_first(self):
        for name in self.SKILLS_WITH_GATE_1:
            with self.subTest(skill=name):
                text = self._skill_text(name)
                self.assertIn("notion-search", text,
                              f"{name} must call notion-search to enumerate T-row page ids "
                              "before fetching them (workspace lacks Business plan for "
                              "notion-query-* tools).")

    def test_each_skill_documents_per_row_fetch(self):
        for name in self.SKILLS_WITH_GATE_1:
            with self.subTest(skill=name):
                text = self._skill_text(name)
                self.assertIn("notion-fetch", text,
                              f"{name} must call notion-fetch on each row page id "
                              "to get the __YES__/__NO__ properties.")
                self.assertIn("__YES__", text,
                              f"{name} must reference __YES__ to correctly interpret "
                              "the checkbox column values.")

    def test_each_skill_warns_against_fetching_db_id_for_rows(self):
        """The classic mistake: assume notion-fetch on the DB id returns
        row data. It returns the SCHEMA. Every SKILL must explicitly
        warn against this after the 2026-07-09 regression."""
        for name in self.SKILLS_WITH_GATE_1:
            with self.subTest(skill=name):
                text = self._skill_text(name)
                # Look for the warning phrase — must mention BOTH the "don't fetch DB id"
                # rule and the SCHEMA reason. Case-insensitive, flexible on markdown.
                text_lower = text.lower()
                self.assertIn("do not", text_lower)
                self.assertIn(TRACKER_DB_ID, text)
                self.assertIn("schema", text_lower,
                              f"{name} must explain that DB-id fetch returns schema.")
                # And the three concepts must appear near each other (within ~500 chars).
                # The DB id may appear multiple times (once in the search step's
                # page_url param, once in the DO NOT warning). Check every
                # occurrence and require at least one to have the warning nearby.
                positions = []
                start = 0
                while True:
                    idx = text.find(TRACKER_DB_ID, start)
                    if idx == -1:
                        break
                    positions.append(idx)
                    start = idx + 1
                found_warning = False
                for idx in positions:
                    window = text[max(0, idx - 500): idx + 500].lower()
                    if "do not" in window and "schema" in window:
                        found_warning = True
                        break
                self.assertTrue(
                    found_warning,
                    f"{name}: at least one DB id mention must have both 'DO NOT' "
                    f"and 'SCHEMA' within 500 chars — that's the warning site.")

    def test_no_skill_uses_business_gated_query_tools(self):
        """These two tools require a Business plan and will 400.
        The SKILLs must not tell the LLM to try them."""
        # SKILLs may still MENTION the tool name (e.g. in the DO NOT warning),
        # so we look for an actual imperative "call ... query_data_sources"
        # rather than any occurrence. The heuristic: if the SKILL says
        # "DO NOT ... query_data_sources", that's fine; but a raw call
        # instruction is not.
        bad_patterns = [
            r"[Cc]all\s+.{0,80}notion-query-data-sources(?!.{0,80}[Ff]ail)",
            r"[Cc]all\s+.{0,80}notion-query-database-view(?!.{0,80}[Ff]ail)",
        ]
        for name in self.SKILLS_WITH_GATE_1:
            text = self._skill_text(name)
            for pattern in bad_patterns:
                with self.subTest(skill=name, pattern=pattern):
                    match = re.search(pattern, text)
                    if match:
                        self.fail(
                            f"{name} instructs an imperative call to a Business-plan-gated "
                            f"tool: `{match.group(0)[:80]}...`. Use notion-search + "
                            "notion-fetch on individual row page ids instead."
                        )


if __name__ == "__main__":
    unittest.main()
