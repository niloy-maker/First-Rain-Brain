import json, sys, time, unittest, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import pipeline_health as ph


class TestValidityAndFreshness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

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


if __name__ == "__main__":
    unittest.main()
