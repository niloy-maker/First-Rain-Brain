"""Regression tests for the 2026-08-13 Telegram-alert redesign.

Enforces the deduplication + compactness contracts so a future edit to any
of the four sync SKILLs can't silently regress back to the old dump-everything
Telegram messages that Niloy called out as noise.

Rules being tested:
- Morning-sync SKILL Step 8 must have the compact template markers
  (🎯 TOP 3, single-line 💰 pulse, PERSISTENT collapse rule) and the
  explicit "do NOT dump the full briefing" instruction.
- Morning-sync SKILL Step 8 must reference persistent_issue_days.py so the
  day-N mechanism actually gets called at runtime.
- Heal-check SKILL Step 6 must have the silent-unless-new template
  and the already-in-today filter rule.
- Neither SKILL may still tell the LLM to "briefing (Step 4) + finance pulse
  (Step 6), concatenated" — that was the old dump behaviour.
"""
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / ".claude" / "scheduled-tasks"


def _read(name: str) -> str:
    return (SKILL_DIR / name / "SKILL.md").read_text()


class TestMorningCompactTemplate(unittest.TestCase):
    """Morning-sync STEP 8 must use the new compact composition rules."""

    text = _read("first-rain-monday-sync")

    def test_step_8_has_compact_template_markers(self):
        for marker in ("🎯 TOP 3", "💰 Op", "📥 COLLECT", "📤 PAY", "🏗 PROJECTS", "🚨 PERSISTENT"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text,
                              f"morning-sync SKILL must contain the '{marker}' compact-format marker")

    def test_step_8_references_persistent_issue_days_helper(self):
        self.assertIn("persistent_issue_days.py", self.text,
                      "morning-sync SKILL must reference persistent_issue_days.py so the "
                      "day-N counter is actually called at compose time")

    def test_step_8_forbids_the_old_dump_pattern(self):
        # The old rule was literally "briefing (Step 4) + finance pulse (Step 6), concatenated".
        # If that line reappears verbatim, the redesign has been undone.
        self.assertNotIn("briefing (Step 4) + finance pulse (Step 6), concatenated", self.text,
                         "morning-sync SKILL must NOT re-adopt the old briefing-dump pattern. "
                         "STEP 8 composes a NEW compact message.")

    def test_step_8_explicitly_warns_against_full_dump(self):
        # Some explicit instruction that says "don't dump the briefing"
        lowered = self.text.lower()
        self.assertTrue(
            "do not dump the full step-4 briefing" in lowered
            or "do not dump the full briefing" in lowered,
            "morning-sync SKILL STEP 8 must explicitly say NOT to dump the full briefing")

    def test_step_8_dedup_rule_stated(self):
        self.assertIn("Every fact appears ONCE", self.text,
                      "morning-sync SKILL STEP 8 must state the 'every fact once' rule")


class TestHealCheckSilentUnlessNew(unittest.TestCase):
    """Heal-check STEP 6 must diff against today's briefing before speaking."""

    text = _read("first-rain-heal-check")

    def test_step_6_references_already_in_today(self):
        self.assertIn("already-in-today", self.text,
                      "heal-check SKILL STEP 6 must call "
                      "persistent_issue_days.py already-in-today to suppress dupes")

    def test_step_6_references_persistent_issue_days_helper(self):
        self.assertIn("persistent_issue_days.py", self.text,
                      "heal-check SKILL STEP 6 must reference persistent_issue_days.py")

    def test_step_6_has_silent_day_template(self):
        # The literal one-line silent-day format
        self.assertIn("✅ 0 new issues", self.text,
                      "heal-check SKILL STEP 6 must include the silent-day one-line format")

    def test_step_6_forbids_healed_section(self):
        # We explicitly removed the 'Healed:' section from Telegram (goes to audit trail only).
        # If it comes back, dedupe with morning briefing gets much harder.
        self.assertIn("No \"healed\" section", self.text,
                      "heal-check SKILL STEP 6 must state that healed items don't go in Telegram")

    def test_step_6_dedup_rule_stated(self):
        self.assertIn("must NOT re-list", self.text,
                      "heal-check SKILL STEP 6 must state the 'no re-listing' rule")


class TestPersistentHelperShipped(unittest.TestCase):
    """The helper both SKILLs reference must actually exist and be executable."""

    HELPER = Path(__file__).resolve().parents[2] / "scripts" / "projects" / "persistent_issue_days.py"

    def test_helper_exists(self):
        self.assertTrue(self.HELPER.exists(),
                        "scripts/projects/persistent_issue_days.py must exist "
                        "— both morning and heal-check SKILLs reference it")

    def test_helper_exposes_days_command(self):
        text = self.HELPER.read_text()
        self.assertIn('cmd == "days"', text)
        self.assertIn('cmd == "already-in-today"', text)

    def test_helper_is_executable(self):
        import os
        self.assertTrue(os.access(self.HELPER, os.X_OK),
                        "persistent_issue_days.py must be chmod +x")


if __name__ == "__main__":
    unittest.main()
