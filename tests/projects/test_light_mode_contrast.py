"""Light-mode contrast regressions (12-Oct-2026).

Bug: the Priority-today column is a dark navy panel in both themes, but the generic
tinted card states (.action-card.critical/.warning/.watch/.success) use LIGHT
backgrounds in light mode while the panel forces white text -> unreadable rows.
Also --text-muted (#a0a0a0) was 2.6:1 on white across dozens of labels.
"""
import re
import unittest
from pathlib import Path

T = (Path(__file__).resolve().parents[2] / "dashboards" / "dashboard-template.html").read_text()


def lum(hexcolor):
    h = hexcolor.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]


def ratio(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


class TestPriorityPanelContrast(unittest.TestCase):
    def test_every_card_state_has_a_dark_override_inside_the_priority_panel(self):
        for state in ("critical", "warning", "watch", "success"):
            m = re.search(r"\.ov-col-priority \.action-card\.%s\{background:rgba\((\d+),(\d+),(\d+),([\d.]+)\)\}" % state, T)
            self.assertIsNotNone(m, f"missing dark-panel override for .action-card.{state}")
            self.assertLessEqual(float(m.group(4)), 0.25, f"{state} tint too opaque — would wash out white text")

    def test_white_text_on_worst_case_tint_meets_aaa(self):
        # worst case: lightest panel stop (#243648) under the strongest tint (critical rgba(255,92,72,.20))
        panel = (0x24, 0x36, 0x48)
        tint = (255, 92, 72, 0.20)
        bg = "#%02x%02x%02x" % tuple(round(tint[i] * tint[3] + panel[i] * (1 - tint[3])) for i in range(3))
        self.assertGreaterEqual(ratio("#ffffff", bg), 7.0)

    def test_show_more_buttons_readable_on_dark_panels(self):
        self.assertIn(".ov-col-priority .pri-more-btn{color:rgba(255,255,255", T)
        self.assertIn(".acct-strip .pri-more-btn{color:rgba(255,255,255", T)


class TestLightTokens(unittest.TestCase):
    def tokens(self):
        m = re.search(r":root\{\s*--bg-primary:[^}]*?--text-tertiary:(#[0-9a-fA-F]{6});--text-muted:(#[0-9a-fA-F]{6});", T, re.S)
        self.assertIsNotNone(m)
        return m.group(1), m.group(2)

    def test_muted_and_tertiary_text_meet_aa_on_white_and_secondary_bg(self):
        tert, muted = self.tokens()
        for name, col in (("tertiary", tert), ("muted", muted)):
            self.assertGreaterEqual(ratio(col, "#ffffff"), 4.5, f"--text-{name} fails AA on white")
            self.assertGreaterEqual(ratio(col, "#f3f3ef"), 4.5, f"--text-{name} fails AA on --bg-secondary")

    def test_hierarchy_preserved(self):
        tert, muted = self.tokens()
        self.assertLess(lum("#4a4a4a"), lum(tert))     # secondary darker than tertiary
        self.assertLess(lum(tert), lum(muted))         # tertiary darker than muted


if __name__ == "__main__":
    unittest.main()
