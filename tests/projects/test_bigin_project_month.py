"""Regression test for the 2026-07-07 exec-coverage blackout.

Root cause of the incident: `fetch_bigin_pipeline.py`'s COQL SELECT clause
never asked for `Project_Month`, so all deals came back without the field.
Downstream `_compute_pipeline_coverage_by_month()` correctly detected zero
dated deals and set `dataAvailable=false` — but Niloy saw a blank strip
with only a warning banner.

These tests pin the contract between the Bigin fetcher and the coverage
computation so a future refactor can't silently break the chain again.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))

from fetch_bigin_pipeline import (
    COQL_PIPELINE_FULL,
    COQL_PIPELINE_NO_PROJECT_MONTH,
    COQL_PIPELINE_FALLBACK,
    _normalize_deal,
)


class TestCoqlIncludesProjectMonth(unittest.TestCase):
    """The FULL query must select Project_Month. If someone drops it, this
    fires — before the code lands in production and blanks the strip again."""

    def test_full_query_selects_project_month(self):
        self.assertIn("Project_Month", COQL_PIPELINE_FULL,
                      "COQL_PIPELINE_FULL must SELECT Project_Month — "
                      "the by-project-month coverage strip depends on it")

    def test_no_project_month_query_omits_it(self):
        # This is the intentional stepdown when Zoho reports the column missing
        self.assertNotIn("Project_Month", COQL_PIPELINE_NO_PROJECT_MONTH,
                         "COQL_PIPELINE_NO_PROJECT_MONTH should NOT select "
                         "Project_Month — it's the fallback when the field is absent")

    def test_minimal_fallback_omits_project_month_and_region(self):
        self.assertNotIn("Project_Month", COQL_PIPELINE_FALLBACK)
        self.assertNotIn("Region", COQL_PIPELINE_FALLBACK)


class TestNormalizeDealPropagatesProjectMonth(unittest.TestCase):
    """`_normalize_deal` must actually populate project_month on the output
    dict — otherwise deals reach `_compute_pipeline_coverage_by_month`
    without the field and every month shows Rs 0."""

    _RAW = {
        "id": "abc",
        "Deal_Name": "test",
        "Account_Name": {"id": "acct1", "Account_Name": "Test Co"},
        "Amount": 500000,
        "Probability": 50,
        "Stage": "Design",
        "Closing_Date": "2026-08-01",
        "Region": "India",
        "Project_Month": "2026-08-20",
    }

    def test_project_month_populated_when_available(self):
        d = _normalize_deal(self._RAW, {}, region_available=True,
                            industry_available=False,
                            project_month_available=True)
        self.assertEqual(d["project_month"], "2026-08-20",
                         "project_month must flow from COQL row to normalized deal")

    def test_project_month_null_when_field_absent(self):
        # When the fallback COQL runs (Project_Month column not in schema),
        # the raw dict won't have it — normalizer must not error, and must
        # emit None so downstream distinguishes "no schema" from "not tagged".
        raw_no_pm = {k: v for k, v in self._RAW.items() if k != "Project_Month"}
        d = _normalize_deal(raw_no_pm, {}, region_available=True,
                            industry_available=False,
                            project_month_available=False)
        self.assertIsNone(d["project_month"])

    def test_project_month_null_when_flag_off_even_if_field_present(self):
        # Defensive: if the flag says the field isn't available, don't leak
        # a random value from a merged/mocked dict.
        d = _normalize_deal(self._RAW, {}, region_available=True,
                            industry_available=False,
                            project_month_available=False)
        self.assertIsNone(d["project_month"])

    def test_backward_compatible_default(self):
        # Legacy callers may not pass project_month_available. Default is False.
        d = _normalize_deal(self._RAW, {}, region_available=True,
                            industry_available=False)
        self.assertIsNone(d["project_month"])


class TestClassifyPreservesProjectMonth(unittest.TestCase):
    """`classify()` iterates deals in-place adding region/industry/bucket/
    weighted. It must NEVER drop project_month — otherwise every re-classify
    (midday, EOD, /finance manual, run_pipeline.py) wipes the field even when
    the morning fetch put it there. This test is the guarantee."""

    def test_classify_preserves_project_month_on_every_deal(self):
        from classify_pipeline import classify
        # Minimal shape mimicking a fresh raw.json from Step 5A
        raw = {
            "deals": [
                {"id": "1", "deal": "CK - x", "amount": 100, "prob": 50,
                 "stage": "Design", "close": "2026-08-01", "region": "India",
                 "industry": None, "project_month": "2026-08-20",
                 "account": "a", "account_name": "A",
                 "created": "2026-01-01", "modified": "2026-01-01"},
                {"id": "2", "deal": "SP - y", "amount": 200, "prob": 30,
                 "stage": "Requirement gathering", "close": "2026-09-01", "region": "India",
                 "industry": None, "project_month": None,  # legitimately untagged
                 "account": "b", "account_name": "B",
                 "created": "2026-01-01", "modified": "2026-01-01"},
            ],
            "meta": {"region_available": True, "industry_available": False,
                     "project_month_available": True,
                     "fetched_at": "2026-07-07T09:00:00", "count": 2}
        }
        # classify() mutates in place AND writes to disk. To avoid touching
        # the real bigin_pipeline_classified.json, run in a temp cwd.
        import os, tempfile, shutil, sys, importlib
        with tempfile.TemporaryDirectory() as tmp:
            (tmp_path := __import__("pathlib").Path(tmp) / "data" / "projects").mkdir(parents=True)
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                # Reload the module so OUTPUT_PATH resolves against tmp cwd
                import classify_pipeline as cp
                importlib.reload(cp)
                result = cp.classify(raw)
            finally:
                os.chdir(old_cwd)
        self.assertEqual(result["deals"][0]["project_month"], "2026-08-20",
                         "classify() must preserve project_month on tagged deals")
        self.assertIsNone(result["deals"][1]["project_month"],
                          "classify() must preserve None for untagged deals (not delete the key)")
        self.assertIn("project_month", result["deals"][1],
                      "the key itself must be present — downstream .get() with default 0 would silently mis-bucket if missing")
        self.assertTrue(result["meta"]["project_month_available"],
                        "meta flag must survive classify")


class TestMorningSyncSkillCoqlHasProjectMonth(unittest.TestCase):
    """The morning-sync SKILL's inline COQL is the ACTUAL production fetch
    path. `fetch_bigin_pipeline.py` (tested above) is used only by the direct-
    REST invocation which requires .env credentials — the SKILL never calls
    it. On 2026-07-07 the SKILL COQL silently dropped Project_Month and
    downstream classify wiped the field from bigin_pipeline_classified.json.
    This canary is what would have caught it."""

    _SKILL_PATH = Path.home() / ".claude" / "scheduled-tasks" / "first-rain-monday-sync" / "SKILL.md"
    _SKILL_REPO_COPY = Path(__file__).resolve().parents[2] / ".claude" / "scheduled-tasks" / "first-rain-monday-sync" / "SKILL.md"

    def _skill_text(self):
        # Prefer the repo copy (guaranteed present in CI); fall back to the
        # live copy for developers running locally.
        if self._SKILL_REPO_COPY.exists():
            return self._SKILL_REPO_COPY.read_text()
        if self._SKILL_PATH.exists():
            return self._SKILL_PATH.read_text()
        self.skipTest("SKILL file not found — running outside a First Rain Mac")

    def test_skill_coql_selects_project_month(self):
        text = self._skill_text()
        self.assertIn("Project_Month", text,
                      "morning-sync SKILL must reference Project_Month "
                      "(SELECT clause + Python transform + required-shape docs). "
                      "Dropping it silently blanks the exec-coverage strip.")

    def test_skill_python_transform_extracts_project_month(self):
        text = self._skill_text()
        # The literal from the transform snippet
        self.assertIn('"project_month": d.get("Project_Month")', text,
                      "morning-sync SKILL's inline Python transform must map "
                      'Project_Month -> project_month on each deal.')

    def test_skill_meta_declares_project_month_available(self):
        text = self._skill_text()
        self.assertIn("project_month_available", text,
                      "meta object in the SKILL's required-shape and Python "
                      "transform must include project_month_available so "
                      "downstream can tell schema-gap from data-gap.")


if __name__ == "__main__":
    unittest.main()
