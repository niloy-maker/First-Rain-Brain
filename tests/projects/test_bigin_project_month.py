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


if __name__ == "__main__":
    unittest.main()
