import csv
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    actor: str
    tenant_id: str
    action: str  # "login", "logout", "permission_denied", "query_execution", "workspace_create"
    resource_id: str
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "success"  # "success", "denied", "failure"
    details: str = ""


class AuditLoggingService:
    """Enterprise Audit Logging Service maintaining immutable audit records."""

    def __init__(self):
        self._audit_records: List[AuditEvent] = []
        self.max_backlog = 5000

    def record_event(
        self,
        actor: str,
        tenant_id: str,
        action: str,
        resource_id: str,
        status: str = "success",
        details: str = "",
        correlation_id: Optional[str] = None
    ) -> AuditEvent:
        if len(self._audit_records) >= self.max_backlog:
            logger.warning("Audit backlog growing")

        event = AuditEvent(
            actor=actor,
            tenant_id=tenant_id,
            action=action,
            resource_id=resource_id,
            status=status,
            details=details,
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        try:
            self._audit_records.append(event)
            logger.info("Audit event recorded")
            return event
        except Exception as e:
            logger.error("Audit persistence failure")
            raise e

    def get_events(self, tenant_id: str) -> List[AuditEvent]:
        # Enforce tenant isolation for audit queries
        return [e for e in self._audit_records if e.tenant_id == tenant_id]

    def export_to_json(self, tenant_id: str) -> str:
        try:
            events = self.get_events(tenant_id)
            data = [e.model_dump() for e in events]
            res = json.dumps(data, indent=2)
            logger.info("Audit export completed")
            return res
        except Exception as e:
            logger.error("Export failure")
            raise e

    def export_to_csv(self, tenant_id: str) -> str:
        import io
        try:
            events = self.get_events(tenant_id)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["event_id", "timestamp", "actor", "tenant_id", "action", "resource_id", "status", "details", "correlation_id"])
            for e in events:
                writer.writerow([
                    e.event_id, e.timestamp, e.actor, e.tenant_id,
                    e.action, e.resource_id, e.status, e.details, e.correlation_id
                ])
            logger.info("Audit export completed")
            return output.getvalue()
        except Exception as e:
            logger.error("Export failure")
            raise e

    def apply_retention_policy(self, max_age_seconds: float):
        now = time.time()
        # Keep only records where timestamp is within retention window
        self._audit_records = [e for e in self._audit_records if (now - e.timestamp) <= max_age_seconds]
