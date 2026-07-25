import unittest
import time
from ecip_core.security.auth_service import AuthenticationService, LocalIdentityProvider


class TestAuthenticationService(unittest.TestCase):

    def setUp(self):
        self.provider = LocalIdentityProvider()
        self.provider.register_user("admin", "admin-pass")
        self.auth_service = AuthenticationService(provider=self.provider)

    def test_successful_login(self):
        tokens = self.auth_service.authenticate_user("admin", "admin-pass")
        self.assertIsNotNone(tokens)
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)

        # Validate access token
        username = self.auth_service.validate_access_token(tokens["access_token"])
        self.assertEqual(username, "admin")

    def test_failed_login(self):
        tokens = self.auth_service.authenticate_user("admin", "wrong-pass")
        self.assertIsNull = self.assertIsNone(tokens)

        tokens_unknown = self.auth_service.authenticate_user("unknown", "pass")
        self.assertIsNone(tokens_unknown)

    def test_token_refresh_and_logout(self):
        tokens = self.auth_service.authenticate_user("admin", "admin-pass")
        self.assertIsNotNone(tokens)

        # Refresh
        refresh_res = self.auth_service.refresh_session(tokens["refresh_token"])
        self.assertIsNotNone(refresh_res)
        self.assertIn("access_token", refresh_res)

        # Logout
        logged_out = self.auth_service.logout(tokens["refresh_token"])
        self.assertTrue(logged_out)

        # Try to refresh after logout
        refresh_res2 = self.auth_service.refresh_session(tokens["refresh_token"])
        self.assertIsNone(refresh_res2)


if __name__ == "__main__":
    unittest.main()
