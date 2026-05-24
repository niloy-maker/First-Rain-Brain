"""SMS feed-health classification.

Tonight's false-confidence bug: the parser reported 'feed LIVE, no new credit' while
the HDFC bank SMS were actually not syncing — because promo SMS (BigBasket/Jio) kept
the OVERALL feed looking live. These tests pin a separate 'bank feed' signal so a
stale bank-sender feed is caught even when other SMS flow.
"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import parse_hdfc_imessages as sms


class TestClassifyFeed(unittest.TestCase):
    def test_both_fresh(self):
        feed, bank, flag = sms.classify_feed(h_any=2.0, h_hdfc=3.0)
        self.assertEqual(feed, "live")
        self.assertEqual(bank, "live")
        self.assertFalse(flag)

    def test_bank_stale_but_phone_live_is_the_trap(self):
        # promos flowing (h_any small) but no bank SMS for days (h_hdfc large)
        feed, bank, flag = sms.classify_feed(h_any=1.0, h_hdfc=96.0)
        self.assertEqual(feed, "live")          # overall phone feed looks fine...
        self.assertEqual(bank, "stale")         # ...but the bank feed is stale
        self.assertTrue(flag)                   # <- the signal that prevents false confidence

    def test_whole_feed_stale(self):
        feed, bank, flag = sms.classify_feed(h_any=48.0, h_hdfc=50.0)
        self.assertEqual(feed, "stale")
        self.assertEqual(bank, "stale")

    def test_no_bank_messages_ever_flags(self):
        feed, bank, flag = sms.classify_feed(h_any=1.0, h_hdfc=None)
        self.assertEqual(feed, "live")
        self.assertEqual(bank, "unknown")
        self.assertTrue(flag)

    def test_no_messages_at_all(self):
        feed, bank, flag = sms.classify_feed(h_any=None, h_hdfc=None)
        self.assertEqual(feed, "unknown")
        self.assertEqual(bank, "unknown")

    def test_bank_threshold_boundary_is_exclusive(self):
        # exactly at the bank threshold is still 'live' (exclusive, matches freshness convention)
        feed, bank, flag = sms.classify_feed(h_any=1.0, h_hdfc=sms.BANK_STALE_THRESHOLD_HOURS)
        self.assertEqual(bank, "live")


if __name__ == "__main__":
    unittest.main()
