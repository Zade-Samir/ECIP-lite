"""
JWT Authentication middleware for the API Gateway.
Validates Bearer tokens using the existing auth_service.
"""
from typing import Optional
from ecip_core.common.logger import get_logger
from ecip_core.security.auth_service import AuthenticationService as _AuthService

logger = get_logger(__name__)

# Shared instance for token verification
_auth_service = _AuthService()


def create_access_token(payload: dict) -> str:
    """Create a JWT access token (helper for tests and internal use)."""
    return _auth_service._generate_jwt(payload)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return _auth_service._verify_jwt(token)
    except Exception:
        return None


class AuthMiddleware:
    """
    Validates JWT Bearer tokens on incoming requests.

    Usage:
        mw = AuthMiddleware(secret_key="...", bypass_paths=["/health", "/api/v1/index"])
        payload = mw.validate("Bearer eyJ...")
        if payload is None:
            raise Unauthorized()
    """

    def __init__(
        self,
        bypass_paths: Optional[list[str]] = None,
    ):
        self.bypass_paths = bypass_paths or ["/health", "/api/v1/health"]

    def should_bypass(self, path: str) -> bool:
        return any(path.startswith(bp) for bp in self.bypass_paths)

    def validate(self, authorization_header: Optional[str]) -> Optional[dict]:
        """
        Validate an Authorization header value.

        Args:
            authorization_header: Value of the Authorization header, e.g. "Bearer <token>"

        Returns:
            Decoded token payload dict, or None if invalid.
        """
        if not authorization_header:
            logger.error("Authentication failure")
            return None

        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.error("Authentication failure")
            return None

        token = parts[1]
        try:
            payload = decode_token(token)
            return payload
        except Exception as e:
            logger.error("Authentication failure")
            return None
