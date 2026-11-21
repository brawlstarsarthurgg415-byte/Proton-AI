import unittest

from proton.core import Proton


class LocalDialogueTests(unittest.TestCase):
    def setUp(self):
        self.proton = Proton()

    def test_simple_greeting_uses_brazilian_style(self):
        self.assertIn("E aí", self.proton.chat("oi"))

    def test_thanks(self):
        self.assertIn("Tamo junto", self.proton.chat("valeu"))

    def test_short_reply_suave(self):
        self.assertIn("já é", self.proton.chat("suave"))

    def test_common_abbreviation(self):
        self.assertIn("Papo reto", self.proton.chat("vdd"))

    def test_slang_and_profanity_are_contextual(self):
        answer = self.proton.chat("vsfd")
        self.assertIn("qual foi", answer)

    def test_maciota_expression(self):
        self.assertIn("sem correria", self.proton.chat("vai na maciota"))

    def test_unknown_question_asks_for_clarification(self):
        answer = self.proton.chat("qual é a capital de Marte?")
        self.assertIn("Explica", answer)


if __name__ == "__main__":
    unittest.main()
