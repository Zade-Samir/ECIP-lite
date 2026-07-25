import unittest
from ecip_core.security.rbac.rbac_service import RBACService


class TestRBAC(unittest.TestCase):

    def setUp(self):
        self.rbac = RBACService()
        self.rbac.assign_role("alice", "Administrator")
        self.rbac.assign_role("bob", "Developer")
        self.rbac.assign_role("charlie", "Viewer")

    def test_role_assignment_and_retrieval(self):
        self.assertEqual(self.rbac.get_user_role("alice"), "Administrator")
        self.assertEqual(self.rbac.get_user_role("bob"), "Developer")

    def test_permission_evaluation(self):
        # Admin should have all permissions
        self.assertTrue(self.rbac.check_permission("alice", "user:admin"))
        self.assertTrue(self.rbac.check_permission("alice", "query:execute"))

        # Developer should have execute and index, but not user:admin
        self.assertTrue(self.rbac.check_permission("bob", "project:index"))
        self.assertTrue(self.rbac.check_permission("bob", "query:execute"))
        self.assertFalse(self.rbac.check_permission("bob", "user:admin"))

        # Viewer should only have read/execute but not index
        self.assertTrue(self.rbac.check_permission("charlie", "query:execute"))
        self.assertFalse(self.rbac.check_permission("charlie", "project:index"))

    def test_unknown_role(self):
        assigned = self.rbac.assign_role("dave", "NonExistentRole")
        self.assertFalse(assigned)


if __name__ == "__main__":
    unittest.main()
