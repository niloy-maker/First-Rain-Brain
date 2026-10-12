"""Desktop sidebar collapse/expand (12-Oct-2026).

Contract: a topbar toggle collapses the nav to a 64px icon rail on desktop, persists the
choice, supports the '[' shortcut, never touches the mobile drawer, and stays accessible.
"""
import re
import unittest
from pathlib import Path

T = (Path(__file__).resolve().parents[2] / "dashboards" / "dashboard-template.html").read_text()


class TestSidebarCollapse(unittest.TestCase):
    def test_toggle_button_is_accessible(self):
        m = re.search(r'<button class="tb-collapse"[^>]*>', T)
        self.assertIsNotNone(m, "collapse button missing")
        tag = m.group(0)
        for attr in ('id="sb-collapse-btn"', 'onclick="toggleSidebarCollapse()"', 'aria-label="Collapse sidebar"',
                     'aria-expanded="true"', 'aria-controls="sidebar"', 'title='):
            self.assertIn(attr, tag)

    def test_label_and_aria_flip_with_state(self):
        self.assertIn('"Expand sidebar"', T)
        self.assertIn('setAttribute("aria-expanded", c ? "false" : "true")', T)

    def test_collapsed_state_is_an_icon_rail_scoped_to_desktop(self):
        css = T[T.index("SIDEBAR COLLAPSE"):T.index("/* ═══ MAIN ═══ */")]
        self.assertIn("@media(min-width:901px){", css)
        self.assertIn(".app.sb-collapsed .sidebar{width:64px}", css)
        # every collapsed rule lives inside the desktop media block, so the mobile drawer is untouched
        outside = css.split("@media(min-width:901px){")[0]
        self.assertNotIn(".sb-collapsed .sb-btn", outside)
        self.assertNotIn(".sb-collapsed .sidebar", outside)
        # hidden on mobile by default; only shown >900px
        self.assertIn(".tb-collapse{display:none;", css)

    def test_sidebar_width_is_animated(self):
        self.assertIn("transition:transform var(--t-slow),width var(--t-slow)", T)

    def test_nav_buttons_have_tooltips_for_icon_only_mode(self):
        self.assertRegex(T, r'<button class="sb-btn" data-page="\' \+ n\.id \+ \'" title="')

    def test_state_persists_and_degrades_gracefully(self):
        self.assertIn('localStorage.getItem("fr_sb_collapsed")==="1"', T)      # early restore, no flash
        self.assertIn('localStorage.setItem("fr_sb_collapsed"', T)
        for m in re.finditer(r"localStorage\.(get|set)Item\(\"fr_sb_collapsed\"", T):
            window = T[max(0, m.start() - 160):m.start()]
            self.assertIn("try", window, "localStorage access must be wrapped in try/catch")

    def test_keyboard_shortcut_ignores_typing_contexts(self):
        i = T.index('e.key !== "["')
        block = T[i:i + 420]
        for guard in ("e.metaKey", "e.ctrlKey", "e.altKey", "INPUT", "TEXTAREA", "SELECT", "isContentEditable"):
            self.assertIn(guard, block)

    def test_charts_get_a_resize_nudge_after_the_transition(self):
        self.assertIn('window.dispatchEvent(new Event("resize"))', T)

    def test_urgent_badges_survive_as_dots_when_collapsed(self):
        self.assertRegex(T, r"\.app\.sb-collapsed \.sb-badge\{position:absolute[^}]*width:8px;height:8px")
        self.assertIn(".app.sb-collapsed .sb-badge.ok{display:none}", T)


if __name__ == "__main__":
    unittest.main()
