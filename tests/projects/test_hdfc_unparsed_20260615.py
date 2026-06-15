"""
test_hdfc_unparsed_20260615.py

Regression tests for the 19 HDFC alert templates the parser was dropping as of
the 15 Jun 2026 heal-check (sender alerts@hdfcbank.bank.in, "no_pattern_matched").

Each case is a real snippet pulled from data/projects/sheet_bank_transactions.json
meta.warnings on 15 Jun 2026. The parser must now either:
  - parse it to a transaction (kept if account in 0247/0241, else filtered), or
  - recognise it as a non-transactional admin notice (skipped),
and NEVER leave it in meta.warnings as unparseable.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import parse_hdfc_emails as hp

GREET = "Dear Customer, Greetings from HDFC Bank! "


def _msg(snippet, subject="View: Account update for your HDFC Bank A/c"):
    return {
        "id": "t",
        "sender": "alerts@hdfcbank.bank.in",
        "subject": subject,
        "snippet": GREET + snippet,
        "date": "2026-05-19T10:00:00+05:30",
    }


class TestUpiDebitPermissive(unittest.TestCase):
    """UPI debits from personal account 4401 — must parse, then route to filtered."""

    def test_upi_with_vpa_and_name_and_date(self):
        t = hp.parse_hdfc_email(_msg(
            "Rs.49500.00 is debited from your account ending 4401 towards VPA "
            "niloysingle@kotak (NILOY DEBNATH) on 09-05-26. UPI transaction reference no.: 612970775165.",
            subject="You have done a UPI txn. Check details!"))
        self.assertIsNotNone(t)
        self.assertEqual(t["direction"], "debit")
        self.assertEqual(t["account"], "4401")
        self.assertAlmostEqual(t["amount"], 49500.0, places=2)

    def test_upi_with_vpa_no_name_no_date(self):
        t = hp.parse_hdfc_email(_msg(
            "Rs.86235.00 is debited from your account ending 4401 towards VPA "
            "makemytrip.razorpay@hdfcbank", subject="You have done a UPI txn. Check details!"))
        self.assertIsNotNone(t)
        self.assertEqual(t["direction"], "debit")
        self.assertEqual(t["account"], "4401")
        self.assertAlmostEqual(t["amount"], 86235.0, places=2)

    def test_upi_no_vpa_no_your(self):
        t = hp.parse_hdfc_email(_msg(
            "Rs.20000.00 debited from account ending 4401",
            subject="You have done a UPI txn. Check details!"))
        self.assertIsNotNone(t)
        self.assertEqual(t["direction"], "debit")
        self.assertEqual(t["account"], "4401")
        self.assertAlmostEqual(t["amount"], 20000.0, places=2)


class TestDeductNarration(unittest.TestCase):
    """'Rs. INR X deducted from XXNNNN - NARRATION' account-update debits."""

    def test_expense_debit_kept(self):
        t = hp.parse_hdfc_email(_msg("Rs. INR 17500.00 deducted from XX0247 - HP Laptop Kalyan"))
        self.assertIsNotNone(t)
        self.assertEqual(t["direction"], "debit")
        self.assertEqual(t["account"], "0247")
        self.assertAlmostEqual(t["amount"], 17500.0, places=2)

    def test_indian_lakh_format_amount(self):
        t = hp.parse_hdfc_email(_msg("Rs. INR 1,05860.00 deducted from XX0247 - Office Exp 21Apr to 20May26"))
        self.assertIsNotNone(t)
        self.assertAlmostEqual(t["amount"], 105860.0, places=2)
        self.assertEqual(t["account"], "0247")

    def test_fd_booking_is_internal_not_burn(self):
        """Booking an FD moves cash to own treasury — must NOT count as a P&L debit."""
        t = hp.parse_hdfc_email(_msg("Rs. INR 15,00000.00 deducted from XX0247 - FD Booked XXXXXXXXXX7334"))
        self.assertIsNotNone(t)
        self.assertAlmostEqual(t["amount"], 1500000.0, places=2)
        self.assertNotEqual(t["direction"], "debit")  # excluded from debit totals

    def test_ca_to_od_is_internal_transfer(self):
        t = hp.parse_hdfc_email(_msg("Rs. INR 9,00000.00 deducted from XX0247 - Fund trf CA to OD XXXXXXXXXX0241"))
        self.assertIsNotNone(t)
        self.assertEqual(t["direction"], "internal_transfer")
        self.assertAlmostEqual(t["amount"], 900000.0, places=2)


class TestChequeShortForm(unittest.TestCase):
    def test_short_cheque_cleared(self):
        t = hp.parse_hdfc_email(_msg(
            "cheque no. 000000000039 has been successfully cleared, "
            "Rs. INR 1,25000.00 deducted from XX0247"))
        self.assertIsNotNone(t)
        self.assertEqual(t["direction"], "debit")
        self.assertAlmostEqual(t["amount"], 125000.0, places=2)


class TestBalanceSnapshotVariant(unittest.TestCase):
    def test_balance_in_xxacct(self):
        t = hp.parse_hdfc_email(_msg("Available balance in XX0247 is Rs. INR 4,22104.17 as on 19-MAY-26"))
        self.assertIsNotNone(t)
        self.assertEqual(t["type"], "BALANCE_SNAPSHOT")
        self.assertEqual(t["account"], "0247")
        self.assertAlmostEqual(t["amount"], 422104.17, places=2)


class TestAdminNoticeSkipped(unittest.TestCase):
    def test_netbanking_password_reset_is_admin(self):
        m = _msg("Account update for your HDFC Bank A/c - NetBanking password reset")
        self.assertIsNone(hp.parse_hdfc_email(m))
        self.assertTrue(hp._is_admin_notice(m["subject"], m["snippet"]))


class TestNoUnparseableRemain(unittest.TestCase):
    """End-to-end: feed all 19 through parse_threads — zero must remain unparseable."""

    SNIPPETS = [
        ("Rs.86235.00 is debited from your account ending 4401 towards VPA makemytrip.razorpay@hdfcbank", "UPI txn"),
        ("Rs.49500.00 is debited from your account ending 4401 towards VPA niloysingle@kotak (NILOY DEBNATH) on 09-05-26.", "UPI txn"),
        ("Rs.8335.30 is debited from your account ending 4401 towards VPA radissonbluresortand", "UPI txn"),
        ("Account update for your HDFC Bank A/c - NetBanking password reset", "Account update"),
        ("cheque no. 000000000039 has been successfully cleared, Rs. INR 1,25000.00 deducted from XX0247", "Account update"),
        ("Rs.49500.00 is debited from your account ending 4401", "UPI txn"),
        ("Rs.20000.00 debited from account ending 4401", "UPI txn"),
        ("Rs.49500.00 debited from account ending 4401", "UPI txn"),
        ("Rs. INR 17500.00 deducted from XX0247 - HP Laptop Kalyan", "Account update"),
        ("Rs. INR 15,00000.00 deducted from XX0247 - FD Booked XXXXXXXXXX7334", "Account update"),
        ("Rs. INR 15,00000.00 deducted from XX0247 - FD Booked XXXXXXXXXX0621", "Account update"),
        ("Rs. INR 15,00000.00 deducted from XX0247 - FD Booked XXXXXXXXXX1920", "Account update"),
        ("Rs. INR 59999.00 deducted from XX0247 - MahindraCar ExtendWarran", "Account update"),
        ("Rs. INR 1,05860.00 deducted from XX0247 - Office Exp 21Apr to 20May26", "Account update"),
        ("Rs. INR 6,25000.00 deducted from XX0247 - Fund trf CA to OD XXXXXXXXXX0241", "Account update"),
        ("Available balance in XX0247 is Rs. INR 4,22104.17 as on 19-MAY-26", "Account update"),
        ("Available balance in XX2852 is Rs. INR 1,01000.00 as on 19-MAY-26", "Account update"),
        ("Rs. INR 40000.00 deducted from XX4401 - ACH MF", "Account update"),
        ("Rs. INR 9,00000.00 deducted from XX0247 - Fund trf CA to OD XXXXXXXXXX0241", "Account update"),
    ]

    def test_zero_unparseable(self):
        threads = {"threads": [{"messages": [_msg(s, subj) for s, subj in self.SNIPPETS]}]}
        result = hp.parse_threads(threads)
        warns = result["meta"]["warnings"]
        self.assertEqual(result["meta"]["unparseableCount"], 0,
                         msg="Still unparseable:\n" + "\n".join(w["snippet"] for w in warns))


if __name__ == "__main__":
    unittest.main()
