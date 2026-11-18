import tempfile
import unittest
from pathlib import Path

from proton.curriculum import CURRICULUM, subjects
from proton.study import StudySession


class StudySessionTests(unittest.TestCase):
    def test_curriculum_covers_requested_areas(self):
        names = set(subjects())
        self.assertTrue({"Programação", "Astronomia", "Ciências", "História", "Inglês", "Geografia"} <= names)
        self.assertGreaterEqual(len(CURRICULUM), 10)

    def test_short_session_saves_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            state = StudySession(path).run(hours=0.001, interval_seconds=0, max_cycles=3)
            self.assertEqual(state["reviews"], 3)
            self.assertTrue(path.exists())
            loaded = StudySession(path).state
            self.assertEqual(loaded["reviews"], 3)

    def test_invalid_duration_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                StudySession(Path(directory) / "progress.json").run(hours=0)


if __name__ == "__main__":
    unittest.main()
