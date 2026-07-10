"""Internal OD<->CA fund-transfer classification (both HDFC parsers).

Tonight's real bug: a ₹3.25L OD draw (0241 OD -> 0247 CA, then paid to a vendor)
was reported as a 'possible payment received'. These tests pin the narrow detection
rule: classify as internal ONLY on 'OD to CA'/'CA to OD' or own-name 'FIRST RAIN'
+ a transfer phrase. A bare client 'FT-' fund-transfer payment must STAY a credit.
"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import parse_hdfc_imessages as sms
import parse_hdfc_emails as eml

# Real texts from 24 May 2026
SMS_CREDIT_LEG = ("Update! INR 3,25,000.00 deposited in HDFC Bank A/c XX0247 on 24-MAY-26 "
                  "for FIRST RAIN EXH-Fund trf OD to CA.Avl bal INR 3,73,081.77. "
                  "Cheque deposits in A/C are subject to clearing")
SMS_DEBIT_LEG = ("UPDATE: INR 3,25,000.00 debited from HDFC Bank XX0241 on 24-MAY-26. "
                 "Info: XXXXXXXXXX0247-Fund trf from OD to CA. Avl bal:INR -6,25,000.00")
# A genuine client payment by fund transfer — must NOT be flagged internal
SMS_CLIENT_CREDIT = ("Update! INR 5,00,000.00 deposited in HDFC Bank A/c XX0247 on 24-MAY-26 "
                     "for FT-MESSUNG SYSTEMS PRIVATE LIMITED. Avl bal INR 9,00,000.00")
SMS_NORMAL_DEBIT = "INR 12,500.00 debited from HDFC Bank A/c XX0247 on 24-MAY-26 towards vendor payment"


class TestSmsInternalTransfer(unittest.TestCase):
    def test_credit_leg_is_internal(self):
        self.assertEqual(sms.parse_txn_type(SMS_CREDIT_LEG), "internal_transfer")

    def test_debit_leg_is_internal(self):
        self.assertEqual(sms.parse_txn_type(SMS_DEBIT_LEG), "internal_transfer")

    def test_client_fund_transfer_stays_credit(self):
        # "FT-" client payment, no OD<->CA / FIRST RAIN marker -> must remain a credit
        self.assertEqual(sms.parse_txn_type(SMS_CLIENT_CREDIT), "credit")

    def test_normal_debit_stays_debit(self):
        self.assertEqual(sms.parse_txn_type(SMS_NORMAL_DEBIT), "debit")

    def test_is_internal_transfer_helper(self):
        self.assertTrue(sms.is_internal_transfer(SMS_CREDIT_LEG))
        self.assertTrue(sms.is_internal_transfer(SMS_DEBIT_LEG))
        self.assertFalse(sms.is_internal_transfer(SMS_CLIENT_CREDIT))


class TestEmailInternalTransfer(unittest.TestCase):
    def test_helper_anchors_narrowly(self):
        self.assertTrue(eml._is_internal_transfer("... Fund trf OD to CA ..."))
        self.assertTrue(eml._is_internal_transfer("FIRST RAIN EXH fund transfer to OD"))
        # bare client fund transfer / FT- must NOT match
        self.assertFalse(eml._is_internal_transfer("Rs 5,00,000 added from FT-MESSUNG SYSTEMS"))
        self.assertFalse(eml._is_internal_transfer("NEFT credit from ACME CORP"))

    def test_parse_hdfc_email_overrides_credit_to_internal(self):
        # A credit-template email whose narration carries the OD<->CA marker
        msg = {
            "id": "m1",
            "sender": "alerts@hdfcbank.bank.in",
            "subject": "HDFC Bank: Account update",
            "snippet": ("Rs. INR 3,25,000.00 has been successfully added to your account "
                        "ending XX0247 from FIRST RAIN EXH-Fund trf OD to CA"),
        }
        txn = eml.parse_hdfc_email(msg)
        self.assertIsNotNone(txn)
        self.assertEqual(txn["direction"], "internal_transfer")
        self.assertEqual(txn["type"], "INTERNAL_TRANSFER")
        self.assertEqual(txn["account"], "0247")

    def test_parse_hdfc_email_keeps_client_credit(self):
        # Same template, genuine client payer -> must stay a credit
        msg = {
            "id": "m2",
            "sender": "alerts@hdfcbank.bank.in",
            "subject": "HDFC Bank: Account update",
            "snippet": ("Rs. INR 5,00,000.00 has been successfully added to your account "
                        "ending XX0247 from FT-MESSUNG SYSTEMS PRIVATE LIMITED"),
        }
        txn = eml.parse_hdfc_email(msg)
        self.assertIsNotNone(txn)
        self.assertEqual(txn["direction"], "credit")


if __name__ == "__main__":
    unittest.main()
