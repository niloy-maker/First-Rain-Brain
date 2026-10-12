"""Contract tests pinning the 06/07-Aug-2026 dashboard design & logic.

These fail loudly if a future edit (or template regression) silently drops:
  - the grouped Collect/Pay/Statutory UIs with sort toggles
  - the priority grouping + txn show-more expanders
  - the Health vendor breakdown (India/Intl) + structural scoring fields
  - the builder's open-book filters, filed-statutory exclusion, vendor
    aliasing, and won-deal↔sheet matching exports
Run: python3 -m unittest tests.projects.test_dashboard_contract
"""
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "projects"))

TEMPLATE = REPO / "dashboards" / "dashboard-template.html"

# One entry per UI feature shipped 06/07-Aug-2026. If a marker vanishes from
# the template, the corresponding page section is gone — fail the build review.
UI_MARKERS = [
    "priGroups",              # Overview priority grouping
    "pri-more-btn",           # expander (priority + txn feed)
    "more transactions",      # HDFC txn show-more
    "sort-toggle",            # shared sort toggle control
    "_renderPayList",         # Pay vendor grouping
    "_renderRecList",         # Collect client grouping
    "_renderStatList",        # Statutory type grouping
    "CCB",                    # Credit-card strip / Cards tab / card plan (12-Oct-2026)
    "page-cards",             # Cards tab container
    "est-tag",                # statutory EST tags
    "statUnpaid",             # filed-statutory exclusion in JS
    "vcp-grid",               # Health vendor CP breakdown panel
    "wonDealIdsNotInSheet",   # robust won↔sheet dedup consumption
    "33% India / 38% intl",   # economics pod on governance floors
    "SDR engine live",        # hunter engine context (Aug-2026)
]


class TemplateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tpl = TEMPLATE.read_text(encoding="utf-8")

    def test_single_placeholder(self):
        self.assertEqual(self.tpl.count("{{CASHFLOW_JSON}}"), 1)

    def test_ui_markers_present(self):
        missing = [m for m in UI_MARKERS if m not in self.tpl]
        self.assertEqual(missing, [], f"template lost UI markers: {missing}")

    def test_no_resurrected_hardcodes(self):
        for stale in ["4393658", "CK owns 55%", "India CM at 46.8",
                      "Amaara at 21% CM", "30% construction floor",
                      "Hire two sales hunters"]:
            self.assertNotIn(stale, self.tpl, f"stale hardcode back: {stale}")


class BuilderContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_cashflow_json as b
        cls.b = b

    def test_vendor_alias_merges_rahul_exporacle(self):
        self.assertEqual(self.b._canon_vendor("Rahul"),
                         self.b._canon_vendor("Exporacle"))

    def test_statutory_filed_excluded_and_rolled_forward(self):
        rows = [
            {"status": "filed", "dueDate": "2026-08-20", "amountPayable": 100},
            {"status": "projected", "dueDate": "2026-05-20", "amountPayable": 50},
        ]
        out = self.b._monthly_statutory_from_obligations(rows, "2026-08", "2027-03")
        self.assertEqual(out, {"2026-08": 50.0})  # filed dropped, overdue rolls fwd

    def test_derived_exports_new_fields(self):
        # Integration against the repo's cached data files.
        bigin = json.loads((REPO / "data/projects/bigin_pipeline_classified.json").read_text())
        projects = json.loads((REPO / "data/projects/sheet_projects.json").read_text())
        finance = self.b._load_finance()
        derived = self.b._compute_derived(
            bigin, {"projects": projects.get("projects", [])}, finance)
        for key in ["vendorConcentration", "vendorCpBreakdown",
                    "vendorOpenDuesTop", "vendorUpcomingUninvoiced",
                    "wonDealIdsNotInSheet", "secureConcentration"]:
            self.assertIn(key, derived, f"derived lost export: {key}")
        # Concentration must use the live pipeline (dilution bug guard):
        # denominator excludes lost/junk buckets.
        deals = bigin.get("deals", [])
        live = sum(float(d.get("amount") or 0) for d in deals
                   if d.get("bucket") not in ("lost", "junk"))
        sec = sum(float(d.get("amount") or 0) for d in deals
                  if d.get("bucket") not in ("lost", "junk")
                  and d.get("account_name") == "Secure Meters Pvt Ltd")
        if live > 0:
            self.assertAlmostEqual(derived["secureConcentration"], sec / live, places=6)

    def test_open_book_filters(self):
        finance = self.b._load_finance()
        for r in finance["receivables"]:
            self.assertNotIn((r.get("status") or "").lower(), ("paid", "closed"))
            self.assertGreaterEqual(float(r.get("balance") or 0), 1)
        for p in finance["payables"]:
            self.assertNotEqual((p.get("status") or "").lower(), "paid")
            self.assertGreaterEqual(float(p.get("balance", p.get("amount", 0)) or 0), 1)


if __name__ == "__main__":
    unittest.main()
