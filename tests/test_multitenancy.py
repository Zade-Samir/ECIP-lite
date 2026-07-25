import unittest
from ecip_core.security.tenant_context import TenantContextManager


class TestMultitenancy(unittest.TestCase):

    def setUp(self):
        self.manager = TenantContextManager()
        self.manager.register_tenant("tenant_a", "Company A", quota_limit=2)
        self.manager.register_tenant("tenant_b", "Company B")

    def test_tenant_resolution_and_setting(self):
        self.manager.set_current_tenant("tenant_a")
        self.assertEqual(self.manager.get_current_tenant_id(), "tenant_a")

    def test_workspace_ownership_and_isolation(self):
        self.manager.add_workspace_to_tenant("tenant_a", "proj_1")
        self.manager.add_workspace_to_tenant("tenant_a", "proj_2")

        # Set context to tenant A
        self.manager.set_current_tenant("tenant_a")
        self.assertTrue(self.manager.check_workspace_access("proj_1"))
        self.assertTrue(self.manager.check_workspace_access("proj_2"))

        # Set context to tenant B
        self.manager.set_current_tenant("tenant_b")
        # Should deny access since B doesn't own A's workspaces
        self.assertFalse(self.manager.check_workspace_access("proj_1"))

    def test_tenant_quota_limits(self):
        self.manager.add_workspace_to_tenant("tenant_a", "proj_1")
        self.manager.add_workspace_to_tenant("tenant_a", "proj_2")

        with self.assertRaises(ValueError):
            # Limit is 2, so third should throw quota error
            self.manager.add_workspace_to_tenant("tenant_a", "proj_3")


if __name__ == "__main__":
    unittest.main()
