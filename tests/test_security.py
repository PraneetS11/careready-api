import unittest

from app.core.security import hash_password, verify_password


class SecurityTests(unittest.TestCase):
    def test_password_accepts_correct_and_rejects_wrong(self):
        hashed = hash_password("Fictional-correct-password")
        self.assertTrue(verify_password("Fictional-correct-password", hashed))
        self.assertFalse(verify_password("Fictional-wrong-password", hashed))
