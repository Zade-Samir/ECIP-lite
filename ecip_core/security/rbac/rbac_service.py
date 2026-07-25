from typing import Dict, Set, List, Optional
from ecip_core.common.logger import get_logger
from ecip_core.security.models.rbac_models import Role

logger = get_logger(__name__)

# Predefined Roles
DEFAULT_ROLES = {
    "Administrator": Role(
        name="Administrator",
        permissions={
            "workspace:read", "workspace:write", "workspace:admin",
            "project:index", "query:execute", "graph:admin",
            "user:admin", "config:read", "config:write", "diagnostics:execute"
        }
    ),
    "Maintainer": Role(
        name="Maintainer",
        permissions={
            "workspace:read", "workspace:write", "project:index",
            "query:execute", "config:read", "diagnostics:execute"
        }
    ),
    "Developer": Role(
        name="Developer",
        permissions={"workspace:read", "project:index", "query:execute"}
    ),
    "Reviewer": Role(
        name="Reviewer",
        permissions={"workspace:read", "query:execute"}
    ),
    "Viewer": Role(
        name="Viewer",
        permissions={"workspace:read", "query:execute"}
    ),
    "Service Account": Role(
        name="Service Account",
        permissions={"query:execute", "project:index"}
    )
}


class RBACService:
    """Enterprise Role-Based Access Control (RBAC) Service."""

    def __init__(self):
        self.roles = DEFAULT_ROLES
        self.user_roles: Dict[str, str] = {} # username -> role name
        self.permission_cache: Dict[str, Set[str]] = {} # username -> resolved permissions cache

    def assign_role(self, username: str, role_name: str) -> bool:
        if role_name not in self.roles:
            logger.warning("Unknown role")
            return False
        
        self.user_roles[username] = role_name
        # Invalidate cache
        self.permission_cache.pop(username, None)
        logger.info("Role assigned")
        return True

    def get_user_role(self, username: str) -> Optional[str]:
        return self.user_roles.get(username)

    def get_resolved_permissions(self, username: str) -> Set[str]:
        if username in self.permission_cache:
            return self.permission_cache[username]

        role_name = self.user_roles.get(username)
        if not role_name:
            return set()

        resolved = self._resolve_role_permissions(role_name)
        self.permission_cache[username] = resolved
        return resolved

    def check_permission(self, username: str, permission: str) -> bool:
        try:
            logger.info("Permission evaluated")
            permissions = self.get_resolved_permissions(username)
            
            if permission in permissions:
                logger.info("Authorization granted")
                return True
            
            logger.warning("Permission denied")
            return False
        except Exception as e:
            logger.error("Policy evaluation failure")
            raise e

    def _resolve_role_permissions(self, role_name: str) -> Set[str]:
        role = self.roles.get(role_name)
        if not role:
            return set()

        permissions = set(role.permissions)
        # Recursively resolve any inherited roles if present
        for inherited_role in role.inherits:
            permissions.update(self._resolve_role_permissions(inherited_role))
            
        return permissions
