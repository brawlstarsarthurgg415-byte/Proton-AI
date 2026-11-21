import unittest

from proton.core import Proton


class LocalDialogueTests(unittest.TestCase):
    def setUp(self):
        self.proton = Proton()

    def test_simple_greeting(self):
        self.assertIn("Suave", self.proton.chat("oi"))

    def test_thanks(self):
        self.assertIn("Tamo junto", self.proton.chat("valeu"))

    def test_unknown_question_is_honest(self):
        answer = self.proton.chat("qual é a capital de Marte?")
        self.assertIn("aprendendo", answer)


if __name__ == "__main__":
    unittest.main()
