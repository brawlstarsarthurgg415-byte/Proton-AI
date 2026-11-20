import unittest

from proton.personality import BrazilianPersonality


class BrazilianPersonalityTests(unittest.TestCase):
    def test_greeting_uses_informal_brazilian_portuguese(self):
        bot = BrazilianPersonality()
        self.assertIn("resenha", bot.reply("E aí, Proton?"))

    def test_banter_remembers_insult_for_next_turns(self):
        bot = BrazilianPersonality()
        first = bot.reply("Você é mó chato")
        second = bot.reply("E aí, beleza?")
        self.assertIn("OLOCO", first)
        self.assertIn("ofensa", second)

    def test_apology_resets_playful_offense(self):
        bot = BrazilianPersonality()
        bot.reply("Você é feio")
        answer = bot.reply("Foi mal, tô brincando")
        self.assertIn("perdoado", answer)
        self.assertIn("resenha", bot.reply("E aí?"))

    def test_empty_message_gets_reply(self):
        self.assertIn("Manda", BrazilianPersonality().reply("   "))


if __name__ == "__main__":
    unittest.main()
