import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from proton import research


class ResearchTests(unittest.TestCase):
    def test_low_score_adds_gap_but_high_score_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            self.assertTrue(research.record_gap("álgebra", 0.3, path=path))
            self.assertFalse(research.record_gap("geometria", 0.95, path=path))
            queue = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(queue[-1]["topic"], "álgebra")
            self.assertIn("lacuna", queue[-1]["reason"])

    def test_duplicate_topic_is_not_added_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            self.assertTrue(research.add_topic("Python", path=path))
            self.assertFalse(research.add_topic("python", path=path))

    def test_research_saves_source_and_deduplicates_revision(self):
        pages = [{
            "pageid": 42, "title": "Python", "url": "https://pt.wikipedia.org/wiki/Python",
            "revision_id": 99, "extract": "Python é uma linguagem de programação. " * 8,
        }]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue = root / "queue.json"
            library = root / "library.jsonl"
            research.add_topic("Python", path=queue)
            with patch.object(research, "search_wikipedia", return_value=pages):
                result = research.research_pending(queue_path=queue, library_path=library, pause_seconds=0)
            self.assertEqual(result["pages_added"], 1)
            record = json.loads(library.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["trust_status"], "unverified_reference")
            self.assertFalse(record["training_eligible"])
            self.assertIn("url", record)
            with patch.object(research, "search_wikipedia", return_value=pages):
                research.add_topic("Python avançado", path=queue)
                result2 = research.research_pending(queue_path=queue, library_path=library, pause_seconds=0)
            self.assertEqual(result2["pages_added"], 0)


if __name__ == "__main__":
    unittest.main()
