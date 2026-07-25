"""
Approval Manager — Approval workflow for destructive operations.
"""
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalRequest:
    request_id: str
    action_name: str
    details: str
    status: ApprovalStatus = ApprovalStatus.PENDING


class ApprovalManager:
    """
    Manages human approval requests for destructive actions.
    """

    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}

    def request_approval(self, action_name: str, details: str = "") -> str:
        req_id = str(uuid.uuid4())
        req = ApprovalRequest(request_id=req_id, action_name=action_name, details=details)
        self._requests[req_id] = req
        logger.warning("Waiting for approval")
        return req_id

    def approve(self, request_id: str) -> bool:
        if request_id not in self._requests:
            return False
        self._requests[request_id].status = ApprovalStatus.APPROVED
        return True

    def reject(self, request_id: str) -> bool:
        if request_id not in self._requests:
            return False
        self._requests[request_id].status = ApprovalStatus.REJECTED
        return True

    def get_status(self, request_id: str) -> Optional[ApprovalStatus]:
        req = self._requests.get(request_id)
        return req.status if req else None
