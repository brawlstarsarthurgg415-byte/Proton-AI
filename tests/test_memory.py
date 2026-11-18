import tempfile
import unittest
from pathlib import Path

from proton.core import Proton
from proton.memory import Memory


class ProtonMemoryTests(unittest.TestCase):
    def test_learn_and_retrieve(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Memory(Path(directory) / "knowledge.json")
            proton = Proton(memory)
            proton.learn("A Terra gira ao redor do Sol.")
            results = proton.ask("Terra Sol")
            self.assertEqual(len(results), 1)
            self.assertIn("Terra", results[0]["text"])

    def test_empty_question_has_no_results(self):
        with tempfile.TemporaryDirectory() as directory:
            proton = Proton(Memory(Path(directory) / "knowledge.json"))
            proton.learn("Uma anotação qualquer.")
            self.assertEqual(proton.ask("   "), [])

    def test_empty_knowledge_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            proton = Proton(Memory(Path(directory) / "knowledge.json"))
            with self.assertRaises(ValueError):
                proton.learn("   ")


if __name__ == "__main__":
    unittest.main()
