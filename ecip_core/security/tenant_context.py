import contextvars
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class Tenant(BaseModel):
    tenant_id: str
    organization_name: str
    workspace_ids: List[str] = Field(default_factory=list)
    users: List[str] = Field(default_factory=list)
    quota_limit: int = 10  # Maximum workspaces allowed
    status: str = "active"  # "active" or "disabled"


# ContextVar for thread-safe/async-safe tenant context propagation
_current_tenant_id = contextvars.ContextVar("current_tenant_id", default="default_tenant")


class TenantContextManager:
    """Manages multi-tenant workspace registry, context, and quota checks."""

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {
            "default_tenant": Tenant(
                tenant_id="default_tenant",
                organization_name="Default Organization",
                workspace_ids=[],
                users=[]
            )
        }

    def set_current_tenant(self, tenant_id: str):
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            logger.error("Tenant resolution failure")
            raise ValueError(f"Unknown tenant: {tenant_id}")
        
        if tenant.status != "active":
            logger.error("Tenant resolution failure")
            raise ValueError(f"Tenant is disabled: {tenant_id}")

        _current_tenant_id.set(tenant_id)
        logger.info("Tenant resolved")

    def get_current_tenant_id(self) -> str:
        return _current_tenant_id.get()

    def register_tenant(self, tenant_id: str, organization_name: str, quota_limit: int = 10) -> Tenant:
        tenant = Tenant(
            tenant_id=tenant_id,
            organization_name=organization_name,
            quota_limit=quota_limit
        )
        self.tenants[tenant_id] = tenant
        return tenant

    def add_user_to_tenant(self, tenant_id: str, username: str):
        tenant = self.tenants.get(tenant_id)
        if tenant:
            if username not in tenant.users:
                tenant.users.append(username)

    def check_workspace_access(self, workspace_id: str) -> bool:
        tenant_id = self.get_current_tenant_id()
        tenant = self.tenants.get(tenant_id)
        
        # If single-tenant default backward compatibility is active, allow all
        if tenant_id == "default_tenant":
            return True

        if not tenant:
            logger.error("Tenant resolution failure")
            return False

        if workspace_id in tenant.workspace_ids:
            logger.info("Workspace loaded")
            return True

        logger.error("Cross-tenant access detected")
        return False

    def add_workspace_to_tenant(self, tenant_id: str, workspace_id: str):
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            logger.warning("Unknown workspace")
            raise ValueError(f"Tenant not found: {tenant_id}")

        if len(tenant.workspace_ids) >= tenant.quota_limit:
            logger.warning("Tenant quota exceeded")
            raise ValueError("Workspace quota limit exceeded for this tenant")

        if workspace_id not in tenant.workspace_ids:
            tenant.workspace_ids.append(workspace_id)
