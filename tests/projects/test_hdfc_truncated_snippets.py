"""HDFC alerts whose Gmail snippet is cut off before the "... account on DD-MMM-YYYY" tail.

17-Nov-2026 incident: a hand-built email cache carried ~200-char snippets only. The tail-dependent
debit pattern missed, and the generic fallback saw both "deducted" and "added to" and called it a
CREDIT. 35 debits (Rs 44.1L) were counted as credits and a CA->OD transfer (money paid INTO the
overdraft) showed as an OD draw of Rs 54,142.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import parse_hdfc_emails as P
from build_cashflow_json import _derive_od_delta_from_email_transfers

HDR = "Dear Customer, Greetings from HDFC Bank! "
OFFICE = HDR + "Rs. INR 32001.00 is deducted from your account ending XX0247 and added to A2AINT01 - HDFC000000X - C29262161126144955 - MonicaD Office Exp Running sh"
CA_TO_OD = HDR + "Rs. INR 54142.00 is deducted from your account ending XX0247 and added to A2AOWN01 - HDFC000000X - C10302161126150640 - Fund trf CA to OD unimoni -"
FULL = HDR + "Rs. INR 35,568.00 is deducted from your account ending XX0247 and added to A2AINT01 - HDFC000000X - TasleemV 861 - XXXXXXXXXX9398 - TasleemVending account on 29-OCT-2026. The available balance in your account is Rs. INR 28,70,614.61."


def msg(snippet, date="2026-11-16T15:12:05Z", mid="m1"):
    return {"id": mid, "sender": "alerts@hdfcbank.bank.in", "subject": "View: Account update for your HDFC Bank A/c",
            "snippet": snippet, "date": date}


class TestTruncatedDebits(unittest.TestCase):
    def test_truncated_deducted_from_is_a_debit_on_the_message_date(self):
        t = P.parse_hdfc_email(msg(OFFICE))
        self.assertEqual((t["type"], t["direction"], t["amount"], t["account"]), ("ACH_DEBIT", "debit", 32001.0, "0247"))
        self.assertEqual(t["date"], "2026-11-16")

    def test_full_snippet_still_uses_its_printed_date(self):
        t = P.parse_hdfc_email(msg(FULL, date="2026-10-29T08:58:04Z"))
        self.assertEqual((t["type"], t["direction"], t["date"]), ("ACH_DEBIT", "debit", "2026-10-29"))

    def test_ca_to_od_transfer_keeps_debit_as_original_direction(self):
        t = P.parse_hdfc_email(msg(CA_TO_OD))
        self.assertEqual((t["type"], t["direction"], t["originalDirection"]), ("INTERNAL_TRANSFER", "internal_transfer", "debit"))

    def test_generic_fallback_prefers_deducted_over_added_to(self):
        t = P._generic_hdfc_fallback(OFFICE)
        self.assertEqual(t["direction"], "debit")

    def test_real_credits_are_unaffected(self):
        t = P.parse_hdfc_email(msg("Dear Customer, You have received a credit in your HDFC Bank account. Details of the transaction: "
                                   "Amount received: INR 3,26222.44 Account: XX0247 Date: 17-NOV-2026 Reference Details: RTGS Cr-IBKL0000998-SECURE METERS LTD",
                                   date="2026-11-17T11:55:10Z"))
        self.assertEqual((t["direction"], t["amount"], t["date"]), ("credit", 326222.44, "2026-11-17"))


class TestOdNotInflatedByCaToOd(unittest.TestCase):
    def test_ca_to_od_payment_is_a_repay_not_a_draw(self):
        t = P.parse_hdfc_email(msg(CA_TO_OD))
        r = _derive_od_delta_from_email_transfers({"transactions": [t]}, "2026-11-14")
        self.assertTrue(r is None or r["delta"] <= 0)          # never a positive OD draw


if __name__ == "__main__":
    unittest.main()
