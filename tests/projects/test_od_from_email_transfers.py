"""Regression: OD utilization must reflect intraday OD→CA sweeps captured in
HDFC emails, even when Sonal's sheet still says odUtilized=0.

14-Aug-2026 incident: ₹7.5L OD draw happened at 12:39 on 13-Aug (HDFC email
in cache). Sonal's morning sheet snapshot for 13-Aug said odUtilized=0.
Dashboard's OD tile displayed "0% drawn · ₹0 used" for the rest of the day
until a human noticed. Fix nets INTERNAL_TRANSFER credit legs on 0247 since
the sheet's anchor date and overrides odUtilized upward (never downward).
"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
from build_cashflow_json import _derive_od_delta_from_email_transfers
from parse_hdfc_emails import parse_hdfc_email


def _bank_txn(*txns):
    return {"transactions": list(txns)}


def _real_new_deposit_msg(date_iso: str, amount_inr_str: str):
    """Shape a HDFC "New Deposit Alert" email for a FIRST RAIN EXH-Fund credit
    (OD → CA sweep) so parse_hdfc_email emits an INTERNAL_TRANSFER with
    originalDirection preserved."""
    return {
        "id": f"m-{date_iso}",
        "sender": "alerts@hdfcbank.bank.in",
        "subject": "❗ New Deposit Alert: Check your A/c balance now!",
        "snippet": (f"Dear Customer, You have received a credit in your HDFC Bank account. "
                    f"Details of the transaction: Amount received: INR {amount_inr_str} "
                    f"Account: XX0247 Date: {date_iso} "
                    f"Reference Details: FIRST RAIN EXH-Fund"),
    }


class TestParserPreservesOriginalDirection(unittest.TestCase):
    def test_credit_leg_keeps_original_direction(self):
        # Without originalDirection, netting draws vs repays is impossible.
        txn = parse_hdfc_email(_real_new_deposit_msg("13-AUG-2026", "7,50000.00"))
        self.assertIsNotNone(txn)
        self.assertEqual(txn["type"], "INTERNAL_TRANSFER")
        self.assertEqual(txn["direction"], "internal_transfer")
        self.assertEqual(txn["originalDirection"], "credit",
                         "parser must preserve 'credit' as originalDirection so downstream "
                         "can classify this leg as an OD draw")


class TestDeriveOdDeltaFromEmailTransfers(unittest.TestCase):
    def test_single_od_draw_after_anchor(self):
        r = _derive_od_delta_from_email_transfers(
            _bank_txn({"type": "INTERNAL_TRANSFER", "account": "0247",
                       "date": "2026-08-13", "amount": 750000.0,
                       "originalDirection": "credit"}),
            since_date="2026-08-13",
        )
        self.assertIsNotNone(r)
        self.assertEqual(r["delta"], 750000.0)
        self.assertEqual(r["latestDate"], "2026-08-13")
        self.assertEqual(len(r["legs"]), 1)
        self.assertEqual(r["legs"][0]["leg"], "od_draw")

    def test_draws_net_against_repays(self):
        r = _derive_od_delta_from_email_transfers(
            _bank_txn(
                {"type": "INTERNAL_TRANSFER", "account": "0247",
                 "date": "2026-08-13", "amount": 750000.0, "originalDirection": "credit"},
                {"type": "INTERNAL_TRANSFER", "account": "0247",
                 "date": "2026-08-14", "amount": 200000.0, "originalDirection": "debit"},
            ),
            since_date="2026-08-13",
        )
        self.assertEqual(r["delta"], 550000.0)  # 7.5L drawn − 2L repaid
        self.assertEqual(r["latestDate"], "2026-08-14")

    def test_ignores_transfers_before_anchor(self):
        r = _derive_od_delta_from_email_transfers(
            _bank_txn(
                {"type": "INTERNAL_TRANSFER", "account": "0247",
                 "date": "2026-08-01", "amount": 1000000.0, "originalDirection": "credit"},
                {"type": "INTERNAL_TRANSFER", "account": "0247",
                 "date": "2026-08-13", "amount": 750000.0, "originalDirection": "credit"},
            ),
            since_date="2026-08-13",
        )
        # 01-Aug leg is before anchor and must be excluded.
        self.assertEqual(r["delta"], 750000.0)

    def test_ignores_non_internal_transfers(self):
        r = _derive_od_delta_from_email_transfers(
            _bank_txn(
                {"type": "CREDIT", "account": "0247",
                 "date": "2026-08-13", "amount": 500000.0, "originalDirection": "credit"},
                {"type": "INTERNAL_TRANSFER", "account": "0247",
                 "date": "2026-08-13", "amount": 750000.0, "originalDirection": "credit"},
            ),
            since_date="2026-08-13",
        )
        # Only the INTERNAL_TRANSFER counts. External credit ignored.
        self.assertEqual(r["delta"], 750000.0)

    def test_returns_none_when_no_relevant_activity(self):
        self.assertIsNone(_derive_od_delta_from_email_transfers(
            _bank_txn({"type": "CREDIT", "account": "0247",
                       "date": "2026-08-13", "amount": 500000.0}),
            since_date="2026-08-13"))
        self.assertIsNone(_derive_od_delta_from_email_transfers(None, "2026-08-13"))
        self.assertIsNone(_derive_od_delta_from_email_transfers({"transactions": []}, "2026-08-13"))

    def test_end_to_end_parser_plus_derivation(self):
        # Real message shape → parser → derivation. Locks the whole pipeline.
        txn = parse_hdfc_email(_real_new_deposit_msg("13-AUG-2026", "7,50000.00"))
        r = _derive_od_delta_from_email_transfers({"transactions": [txn]},
                                                  since_date="2026-08-13")
        self.assertEqual(r["delta"], 750000.0)


if __name__ == "__main__":
    unittest.main()
