import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from proton.collective import (
    CollectiveError, export_training_text, local_review, record_external_review,
    submit,
)


class CollectiveTests(unittest.TestCase):
    def test_submission_is_local_and_not_training_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp)
            with patch("proton.collective.OUTBOX", outbox):
                item = submit(
                    "A documented lesson about photosynthesis and plant energy.",
                    sources=["https://example.org/biology"],
                )
            self.assertEqual(item["status"], "pending_review")
            self.assertFalse(item["training_eligible"])
            self.assertTrue((outbox / f"{item['id']}.json").exists())

    def test_personal_data_is_rejected(self):
        with self.assertRaises(CollectiveError):
            submit("Contact me at person@example.com for this important lesson.", sources=["https://example.org"])

    def test_claim_is_never_marked_as_verified_or_training_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("proton.collective.OUTBOX", Path(tmp)):
                item = submit("I declare that I own the Example Studio brand and project.", kind="ownership_claim")
            self.assertEqual(item["status"], "declaration_unverified")
            self.assertFalse(item["training_eligible"])
            self.assertIn("not proof", item["notice"])

    def test_two_distinct_reviewers_do_not_auto_approve_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp)
            with patch("proton.collective.OUTBOX", outbox):
                item = submit("A sourced lesson describing how plants convert light into chemical energy.", sources=["https://example.org"])
                record_external_review(item["id"], "reviewer-a", "approve", "The cited source supports this specific explanation.")
                updated = record_external_review(item["id"], "reviewer-b", "approve", "I independently checked the source and its relevant context.")
            self.assertEqual(updated["status"], "pending_curator")
            self.assertFalse(updated["training_eligible"])

    def test_training_export_only_includes_explicitly_approved_lessons(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "approved.jsonl"
            rows = [
                {"schema":"proton-lesson-v1","id":"a","kind":"lesson","content":"Approved sourced lesson.","sources":["https://example.org"],"status":"approved","training_eligible":True},
                {"schema":"proton-lesson-v1","id":"b","kind":"lesson","content":"Pending lesson.","sources":["https://example.org"],"status":"pending_review","training_eligible":False},
                {"schema":"proton-lesson-v1","id":"c","kind":"ownership_claim","content":"I own this brand.","sources":[],"status":"approved","training_eligible":False},
            ]
            source.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")
            output = root / "train.txt"
            count = export_training_text(output, approved_path=source)
            self.assertEqual(count, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "Approved sourced lesson.\n")


if __name__ == "__main__":
    unittest.main()
