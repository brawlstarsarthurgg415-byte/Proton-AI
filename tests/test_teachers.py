import tempfile
import unittest
from pathlib import Path

from proton.learning import LearningPipeline
from proton.memory import Memory
from proton.teachers.local import LocalTeacher


class TeacherPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.memory = Memory(Path(self.temp.name) / "knowledge.json")
        self.pipeline = LearningPipeline(self.memory, LocalTeacher(self.memory, max_workers=2))

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_lesson_is_saved_after_review(self):
        item, reports = self.pipeline.submit("A Terra orbita o Sol.", "user")
        self.assertIsNotNone(item)
        self.assertEqual(len(reports), 3)
        self.assertEqual(item["review"], "passed_local_checks")

    def test_short_lesson_is_rejected(self):
        item, reports = self.pipeline.submit("Oi")
        self.assertIsNone(item)
        self.assertFalse(all(report.passed for report in reports))

    def test_duplicate_is_rejected(self):
        self.pipeline.submit("A Terra orbita o Sol.")
        item, reports = self.pipeline.submit("A Terra orbita o Sol.")
        self.assertIsNone(item)
        self.assertTrue(any(report.name == "duplicidade" and not report.passed for report in reports))

    def test_review_does_not_claim_fact_checking(self):
        _, reports = self.pipeline.submit("A Terra orbita o Sol.", "user")
        source_report = next(report for report in reports if report.name == "origem")
        self.assertIn("não comprova", source_report.message)


if __name__ == "__main__":
    unittest.main()
