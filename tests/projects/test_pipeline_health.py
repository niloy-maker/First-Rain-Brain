import json, shutil, sys, time, unittest, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import pipeline_health as ph


class TestValidityAndFreshness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_is_nonempty(self):
        empty = self.tmp / "empty.txt"; empty.write_text("")
        full = self.tmp / "full.txt"; full.write_text("x")
        self.assertFalse(ph.is_nonempty(self.tmp / "missing.txt"))
        self.assertFalse(ph.is_nonempty(empty))
        self.assertTrue(ph.is_nonempty(full))

    def test_is_valid_json_requires_keys(self):
        good = self.tmp / "g.json"; good.write_text(json.dumps({"deals": [], "meta": {}}))
        missing_key = self.tmp / "m.json"; missing_key.write_text(json.dumps({"deals": []}))
        broken = self.tmp / "b.json"; broken.write_text("{not json")
        self.assertTrue(ph.is_valid_json(good, required_keys=("deals", "meta")))
        self.assertFalse(ph.is_valid_json(missing_key, required_keys=("deals", "meta")))
        self.assertFalse(ph.is_valid_json(broken, required_keys=("deals",)))
        self.assertFalse(ph.is_valid_json(self.tmp / "nope.json", required_keys=()))

    def test_freshness_classifies(self):
        p = self.tmp / "x.json"; p.write_text(json.dumps({"a": 1}))
        now = time.time()
        self.assertEqual(ph.freshness(p, 24, now=now), "fresh")
        import os
        old = now - 48 * 3600
        os.utime(p, (old, old))
        self.assertEqual(ph.freshness(p, 24, now=now), "stale")
        self.assertEqual(ph.freshness(self.tmp / "gone.json", 24, now=now), "failed")

    def test_worst_severity(self):
        self.assertEqual(ph.worst("fresh", "stale", "failed"), "failed")
        self.assertEqual(ph.worst("fresh", "stale"), "stale")
        self.assertEqual(ph.worst("fresh"), "fresh")
        self.assertEqual(ph.worst(), "fresh")  # empty -> fresh


class TestLastGood(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.lg = self.tmp / "last_good"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_snapshot_only_when_valid(self):
        good = self.tmp / "a.json"; good.write_text(json.dumps({"k": 1}))
        empty = self.tmp / "b.json"; empty.write_text("")
        self.assertTrue(ph.snapshot_last_good(good, self.lg))
        self.assertTrue((self.lg / "a.json").exists())
        # empty file must NOT be snapshotted (would poison last_good)
        self.assertFalse(ph.snapshot_last_good(empty, self.lg))
        self.assertFalse((self.lg / "b.json").exists())

    def test_restore_returns_false_when_absent(self):
        target = self.tmp / "c.json"
        self.assertFalse(ph.restore_last_good(target, self.lg))

    def test_restore_copies_back(self):
        target = self.tmp / "d.json"; target.write_text(json.dumps({"v": "new-bad"}))
        self.lg.mkdir(parents=True, exist_ok=True)
        (self.lg / "d.json").write_text(json.dumps({"v": "old-good"}))
        self.assertTrue(ph.restore_last_good(target, self.lg))
        self.assertEqual(json.loads(target.read_text())["v"], "old-good")


class TestHealthReport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_overall_green_when_all_fresh(self):
        r = ph.new_report(now=0)
        ph.set_source(r, "bigin", "fresh", age_hours=0.5, detail="122 deals")
        ph.set_source(r, "sheet", "fresh", age_hours=1.0)
        ph.finalize(r)
        self.assertEqual(r["overall"], "green")
        self.assertEqual(r["sources"]["bigin"]["detail"], "122 deals")

    def test_overall_degraded_when_any_stale(self):
        r = ph.new_report(now=0)
        ph.set_source(r, "bigin", "fresh")
        ph.set_source(r, "sheet", "stale", detail="cached xlsx 2d old")
        ph.finalize(r)
        self.assertEqual(r["overall"], "degraded")

    def test_overall_failed_when_any_failed(self):
        r = ph.new_report(now=0)
        ph.set_source(r, "sheet", "stale")
        ph.set_source(r, "hdfc", "failed", detail="emails cache missing")
        ph.finalize(r)
        self.assertEqual(r["overall"], "failed")

    def test_write_health_roundtrips(self):
        r = ph.new_report(now=0)
        ph.set_source(r, "bigin", "fresh")
        ph.finalize(r)
        out = self.tmp / "h.json"
        ph.write_health(r, out)
        back = json.loads(out.read_text())
        self.assertEqual(back["overall"], "green")
        self.assertIn("generated_at", back)


if __name__ == "__main__":
    unittest.main()
