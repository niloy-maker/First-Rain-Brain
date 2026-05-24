"""
test_hdfc_fallback.py
Tests for _generic_hdfc_fallback and _log_unknown_template added in Task 7.

NOTE on schema: the real parse_hdfc_email success dicts use TWO separate keys:
  - "type"      → template name  (e.g. "CREDIT", "NACH_DEBIT", "generic_fallback")
  - "direction" → credit/debit   (e.g. "credit", "debit")
These tests use "direction" (not "type") for credit/debit assertions, matching
the actual parser schema.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
import parse_hdfc_emails as hp


class TestGenericFallback(unittest.TestCase):
    def test_extracts_credit_amount_and_account(self):
        txt = ("Update: An amount of INR 4,54,000.00 has been moved into your "
               "HDFC Bank account ending 0247 on 24-05-2026.")
        result = hp._generic_hdfc_fallback(txt)
        self.assertIsNotNone(result)
        self.assertEqual(result["account"], "0247")
        self.assertAlmostEqual(result["amount"], 454000.0, places=2)
        self.assertEqual(result["direction"], "credit")

    def test_extracts_debit_direction(self):
        txt = "INR 12,500.00 debited from your A/c ending 0241 towards vendor payment."
        result = hp._generic_hdfc_fallback(txt)
        self.assertIsNotNone(result)
        self.assertEqual(result["account"], "0241")
        self.assertEqual(result["direction"], "debit")

    def test_returns_none_when_no_amount(self):
        self.assertIsNone(hp._generic_hdfc_fallback("Your statement is ready to view."))

    def test_returns_none_for_personal_account(self):
        """Accounts not in ALLOWED_ACCOUNTS (0247/0241) must be silently dropped."""
        txt = "INR 5,000.00 credited to your account ending 9999 on 24-05-2026."
        result = hp._generic_hdfc_fallback(txt)
        self.assertIsNone(result)

    def test_returns_none_when_direction_ambiguous(self):
        """No credit/debit hint -> return None, let _log_unknown_template handle it."""
        txt = "INR 1,000.00 processed for account ending 0247."
        result = hp._generic_hdfc_fallback(txt)
        self.assertIsNone(result)

    def test_result_schema_has_required_keys(self):
        """Fallback dict must carry all keys the downstream parse_threads reads."""
        txt = "INR 3,000.00 credited to your account ending 0247 today."
        result = hp._generic_hdfc_fallback(txt)
        self.assertIsNotNone(result)
        for key in ("type", "date", "amount", "direction", "account",
                    "counterparty", "reference", "purpose", "subject", "_sender"):
            self.assertIn(key, result, msg=f"Missing key: {key}")

    def test_type_field_is_template_name(self):
        """'type' should be the template tag 'generic_fallback', not the direction."""
        txt = "INR 2,000.00 debited from your A/c ending 0241."
        result = hp._generic_hdfc_fallback(txt)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "generic_fallback")


class TestLogUnknownTemplate(unittest.TestCase):
    def test_appends_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "hdfc_unknown_templates.txt"
            with patch.object(hp, "_UNKNOWN_TEMPLATES", log_path):
                hp._log_unknown_template("Some novel HDFC template text here.")
            self.assertTrue(log_path.exists())
            content = log_path.read_text()
            self.assertIn("Some novel HDFC template text here.", content)

    def test_deduplication(self):
        """Same snippet should appear only once even if logged twice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "hdfc_unknown_templates.txt"
            with patch.object(hp, "_UNKNOWN_TEMPLATES", log_path):
                hp._log_unknown_template("Duplicate snippet abc.")
                hp._log_unknown_template("Duplicate snippet abc.")
            lines = [l for l in log_path.read_text().splitlines() if l.strip()]
            self.assertEqual(lines.count("Duplicate snippet abc."), 1)

    def test_noop_on_empty_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "hdfc_unknown_templates.txt"
            with patch.object(hp, "_UNKNOWN_TEMPLATES", log_path):
                hp._log_unknown_template("")
                hp._log_unknown_template(None)
            self.assertFalse(log_path.exists())


if __name__ == "__main__":
    unittest.main()
