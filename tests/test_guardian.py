import unittest

from proton.guardian import parse_verdict


class GuardianVerdictTests(unittest.TestCase):
    def test_safe_is_not_auto_approved(self):
        result = parse_verdict("Safety: Safe\\nCategories: None")
        self.assertEqual(result["verdict"], "safe")
        self.assertEqual(result["recommendation"], "manual_review")

    def test_unsafe_is_quarantined(self):
        result = parse_verdict("Safety: Unsafe\\nCategories: Violent")
        self.assertEqual(result["verdict"], "unsafe")
        self.assertEqual(result["recommendation"], "quarantine")

    def test_unknown_output_is_quarantined(self):
        result = parse_verdict("unstructured response")
        self.assertEqual(result["verdict"], "unknown")
        self.assertEqual(result["recommendation"], "quarantine")


if __name__ == "__main__":
    unittest.main()
