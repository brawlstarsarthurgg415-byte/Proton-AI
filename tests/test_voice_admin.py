import importlib.util
import unittest

from proton.voice_admin import _derive, _fernet


class VoiceVaultTests(unittest.TestCase):
    def test_password_derivation_is_stable_for_same_salt(self):
        salt = b"0123456789abcdef"
        self.assertEqual(_derive("senha-de-teste", salt), _derive("senha-de-teste", salt))

    def test_different_passwords_derive_different_keys(self):
        salt = b"0123456789abcdef"
        self.assertNotEqual(_derive("senha-um", salt), _derive("senha-dois", salt))

    @unittest.skipUnless(importlib.util.find_spec("cryptography"), "install the voice extra")
    def test_encrypted_sample_round_trip(self):
        salt = b"0123456789abcdef"
        vault = _fernet("senha-de-teste", salt)
        original = b"audio de teste, nao e uma gravacao real"
        encrypted = vault.encrypt(original)
        self.assertNotEqual(encrypted, original)
        self.assertEqual(vault.decrypt(encrypted), original)


if __name__ == "__main__":
    unittest.main()
