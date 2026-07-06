"""Execution-month pipeline coverage flag (spec 2026-07-06).

Pins the T-10-week thin-month trigger: a month with < floor of live execution
work (won + confirmed + active, bucketed by Bigin Project_Month) must ALERT
inside 10 weeks and INFO at 10-18 weeks.

Regression pinned: a fully-won month must NOT flag. July 2026 had zero open
pipeline but Rs 59.75L of Won work executing - reading a sold-out month as
"empty" was the failure mode the committed+active metric exists to avoid.

First-run safety pinned: before Step 1 of /finance carries Project_Month,
no deal has the field - every month would read Rs 0 and false-ALERT. The
dataAvailable=False guard suppresses all flags in that state.
"""
import sys, unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
from build_cashflow_json import _compute_pipeline_coverage_by_month

TODAY = date(2026, 7, 6)
FLOOR = 4_000_000


def deal(month, amount, bucket="active", stage="Requirement gathering"):
    return {"deal": "x", "project_month": month, "amount": amount,
            "bucket": bucket, "stage": stage}


class TestCoverageSeverity(unittest.TestCase):
    def test_thin_month_inside_10_weeks_alerts(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 1_440_000, "hot", "Price Quote")], TODAY, FLOOR)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["severity"], "ALERT")
        self.assertIn(aug, cov["flags"])

    def test_thin_month_at_14_weeks_is_info(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-10-15", 2_000_000)], TODAY, FLOOR)
        octr = next(m for m in cov["months"] if m["month"] == "2026-10")
        self.assertEqual(octr["severity"], "INFO")

    def test_covered_month_is_ok(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 5_000_000)], TODAY, FLOOR)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["severity"], "OK")

    def test_sold_out_month_won_only_does_not_flag(self):
        # July regression: fully booked with Won work must read as full.
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-07-22", 5_975_000, "won", "Closed Won 26-27")], TODAY, FLOOR)
        jul = next(m for m in cov["months"] if m["month"] == "2026-07")
        self.assertEqual(jul["severity"], "OK")
        self.assertEqual(jul["committedValue"], 5_975_000)

    def test_lost_and_junk_excluded(self):
        deals = [deal("2026-08-26", 1_860_000, "lost", "Closed Lost"),
                 deal("2026-08-05", 9_900_000, "junk", "Not Qualified")]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["value"], 0)
        self.assertEqual(aug["dealCount"], 0)

    def test_far_month_thin_is_quiet(self):
        # ~31 weeks out - distant months are supposed to be thin. No flag.
        cov = _compute_pipeline_coverage_by_month(
            [deal("2027-02-10", 100_000)], TODAY, FLOOR)
        feb = next(m for m in cov["months"] if m["month"] == "2027-02")
        self.assertEqual(feb["severity"], "OK")

    def test_unpriced_deals_counted(self):
        deals = [deal("2026-09-22", 0), deal("2026-09-16", 4_117_195)]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        sep = next(m for m in cov["months"] if m["month"] == "2026-09")
        self.assertEqual(sep["unpricedCount"], 1)
        self.assertEqual(sep["dealCount"], 2)

    def test_missing_project_month_counted_not_bucketed(self):
        deals = [deal("2026-08-20", 1_440_000),
                 {"deal": "no-pm", "amount": 500_000, "bucket": "active",
                  "stage": "Design", "project_month": None}]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        self.assertEqual(cov["missingExecMonthCount"], 1)
        self.assertTrue(cov["dataAvailable"])

    def test_no_project_month_data_at_all_suppresses_flags(self):
        deals = [{"deal": "no-pm", "amount": 500_000, "bucket": "active",
                  "stage": "Design"}]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        self.assertFalse(cov["dataAvailable"])
        self.assertEqual(cov["flags"], [])

    def test_floor_override(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 1_440_000)], TODAY, floor=1_000_000)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["severity"], "OK")

    def test_alerts_precede_infos_in_flags(self):
        deals = [deal("2026-10-15", 100_000), deal("2026-08-20", 100_000)]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        sev = [f["severity"] for f in cov["flags"]]
        self.assertIn("ALERT", sev)
        self.assertIn("INFO", sev)
        first_info = sev.index("INFO")
        self.assertTrue(all(s == "ALERT" for s in sev[:first_info]))
        self.assertTrue(all(s == "INFO" for s in sev[first_info:]))


class TestBriefingSection(unittest.TestCase):
    def _briefing(self, cov):
        from build_cashflow_json import _build_telegram_briefing
        return _build_telegram_briefing(
            op_cash=10_000_000, monthly_burn=1_000_000, treasury=0,
            od_facility=0, od_utilized=0, norm_receivables=[],
            norm_statutory=[], treasury_sweep={}, cf_annual={},
            secure_concentration=0.0, saltwater_concentration=0.0,
            pipeline_coverage=cov,
        )

    def test_flags_render_section(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 1_440_000, "hot", "Price Quote"),
             deal("2026-07-22", 5_975_000, "won", "Closed Won 26-27"),
             deal("2026-09-16", 6_000_000)], TODAY, FLOOR)
        text = self._briefing(cov)
        self.assertIn("EXECUTION COVERAGE", text)
        self.assertIn("Aug'26", text)
        self.assertIn("🔴", text)

    def test_no_flags_no_section(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal(m + "-15", 9_000_000) for m in
             ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]],
            TODAY, FLOOR)
        self.assertEqual(cov["flags"], [])
        self.assertNotIn("EXECUTION COVERAGE", self._briefing(cov))

    def test_no_data_shows_warning_not_alerts(self):
        cov = _compute_pipeline_coverage_by_month(
            [{"deal": "no-pm", "amount": 500_000, "bucket": "active",
              "stage": "Design"}], TODAY, FLOOR)
        text = self._briefing(cov)
        self.assertIn("EXECUTION COVERAGE", text)
        self.assertIn("No Project_Month data", text)
        self.assertNotIn("🔴", text.split("EXECUTION COVERAGE")[1])

    def test_none_coverage_is_safe(self):
        # Callers that don't thread coverage through must not crash.
        self.assertNotIn("EXECUTION COVERAGE", self._briefing(None))


if __name__ == "__main__":
    unittest.main()
