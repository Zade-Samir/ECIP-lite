"""
Privacy Filter — Anonymizes operational analytics events and strips sensitive source code content.
"""
from typing import Any, Dict


class PrivacyFilter:
    """
    Sanitizes analytics payload metadata so no source code or sensitive tokens are stored.
    """

    SENSITIVE_KEYS = {"code", "content", "file_content", "query_text", "prompt", "secret", "password", "token"}

    @classmethod
    def sanitize(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not metadata:
            return {}

        sanitized = {}
        for k, v in metadata.items():
            if k.lower() in cls.SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = cls.sanitize(v)
            elif isinstance(v, str) and len(v) > 250:
                sanitized[k] = v[:250] + "...[TRUNCATED]"
            else:
                sanitized[k] = v

        return sanitized
