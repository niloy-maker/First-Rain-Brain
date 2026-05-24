import json, sys, unittest, tempfile, textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import run_pipeline as rp


def _fake_root(tmp):
    """Build a minimal vault-like tree: scripts/projects + data/projects/last_good."""
    (tmp / "scripts" / "projects").mkdir(parents=True)
    (tmp / "data" / "projects" / "last_good").mkdir(parents=True)
    return tmp


def _write_stage_script(root, name, body):
    p = root / "scripts" / "projects" / name
    p.write_text(textwrap.dedent(body))
    return p


class TestRunStage(unittest.TestCase):
    def setUp(self):
        self.root = _fake_root(Path(tempfile.mkdtemp()))

    def test_success_writes_output_and_reports_ok(self):
        _write_stage_script(self.root, "ok_stage.py", """
            import json, pathlib
            out = pathlib.Path("data/projects/out.json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"ok": True}))
            print("wrote 1 row")
        """)
        stage = rp.Stage("ok", "ok_stage.py", "data/projects/out.json", "bigin")
        ok, detail = rp.run_stage(stage, root=self.root)
        self.assertTrue(ok)
        self.assertTrue((self.root / "data/projects/out.json").exists())

    def test_failure_restores_last_good(self):
        good = self.root / "data/projects/out.json"
        good.write_text(json.dumps({"v": "old-good"}))
        (self.root / "data/projects/last_good/out.json").write_text(json.dumps({"v": "old-good"}))
        _write_stage_script(self.root, "bad_stage.py", """
            import pathlib, sys
            pathlib.Path("data/projects/out.json").write_text("corrupt-half-write")
            sys.exit(1)
        """)
        stage = rp.Stage("bad", "bad_stage.py", "data/projects/out.json", "bigin")
        ok, detail = rp.run_stage(stage, root=self.root)
        self.assertFalse(ok)
        self.assertEqual(json.loads(good.read_text())["v"], "old-good")


import time, os


class TestRunPipeline(unittest.TestCase):
    def setUp(self):
        self.root = _fake_root(Path(tempfile.mkdtemp()))

    def _ok_script(self, name, out_rel):
        _write_stage_script(self.root, name, f"""
            import json, pathlib
            out = pathlib.Path({out_rel!r})
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({{"ok": True}}))
            print("done")
        """)

    def test_one_failure_does_not_stop_others(self):
        self._ok_script("s1.py", "data/projects/a.json")
        _write_stage_script(self.root, "s2.py", "import sys; sys.exit(2)")
        self._ok_script("s3.py", "data/projects/c.json")
        stages = [
            rp.Stage("s1", "s1.py", "data/projects/a.json", "bigin"),
            rp.Stage("s2", "s2.py", "data/projects/b.json", "sheet"),
            rp.Stage("s3", "s3.py", "data/projects/c.json", "drift"),
        ]
        report = rp.run_pipeline(stages, root=self.root, now=time.time())
        self.assertEqual(report["sources"]["bigin"]["status"], "fresh")
        self.assertEqual(report["sources"]["drift"]["status"], "fresh")  # ran despite s2 failing
        self.assertEqual(report["sources"]["sheet"]["status"], "failed")
        self.assertEqual(report["overall"], "failed")
        self.assertTrue((self.root / "data/projects/pipeline_health.json").exists())

    def test_stale_input_downgrades_fresh_stage(self):
        self._ok_script("s.py", "data/projects/out.json")
        inp = self.root / "data/projects/_cache/raw.json"
        inp.parent.mkdir(parents=True, exist_ok=True)
        inp.write_text(json.dumps({"deals": [], "meta": {}}))
        old = time.time() - 48 * 3600
        os.utime(inp, (old, old))
        stage = rp.Stage("s", "s.py", "data/projects/out.json", "bigin",
                         input_path="data/projects/_cache/raw.json", input_max_age=24.0,
                         input_required_keys=("deals", "meta"))
        report = rp.run_pipeline([stage], root=self.root, now=time.time())
        self.assertEqual(report["sources"]["bigin"]["status"], "stale")


if __name__ == "__main__":
    unittest.main()
