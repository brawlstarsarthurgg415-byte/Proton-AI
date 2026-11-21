import unittest

from proton.language_ptbr import normalize_ptbr
from proton.core import Proton


class BrazilianPortugueseNormalizerTests(unittest.TestCase):
    def test_common_chat_abbreviations(self):
        self.assertEqual(normalize_ptbr("vc tbm vai hj?"), "você também vai hoje?")

    def test_slang_is_expanded_for_interpretation(self):
        self.assertEqual(normalize_ptbr("vsfd crl"), "vai se foder caralho")
        self.assertEqual(normalize_ptbr("vdd"), "verdade")

    def test_typo_and_greeting(self):
        self.assertEqual(normalize_ptbr("eai dboas?"), "e aí de boas?")
        self.assertIn("E aí", Proton().chat("eai dboas?"))

    def test_unknown_words_are_preserved(self):
        self.assertEqual(normalize_ptbr("xablau"), "xablau")

    def test_personality_style_stays_brazilian(self):
        answer = Proton().chat("vsfd")
        self.assertIn("KKKKK", answer)
        self.assertIn("qual foi", answer)


if __name__ == "__main__":
    unittest.main()
