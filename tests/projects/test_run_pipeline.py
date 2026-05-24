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


if __name__ == "__main__":
    unittest.main()
