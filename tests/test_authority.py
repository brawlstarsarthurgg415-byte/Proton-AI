import base64
import unittest
from unittest.mock import patch

from proton.authority import _password_hash, _verify_password, _new_totp_secret, _totp, _verify_totp


class AuthorityCryptoTests(unittest.TestCase):
    def test_password_hash_verifies(self):
        encoded = _password_hash("a-private-test-password")
        self.assertTrue(_verify_password("a-private-test-password", encoded))
        self.assertFalse(_verify_password("wrong-password", encoded))

    def test_totp_accepts_current_code(self):
        secret = _new_totp_secret()
        now = 1_800_000_000
        with patch("proton.authority.time.time", return_value=now):
            code = _totp(secret)
            self.assertTrue(_verify_totp(secret, code))
            self.assertFalse(_verify_totp(secret, "000000" if code != "000000" else "111111"))


if __name__ == "__main__":
    unittest.main()
