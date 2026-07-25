import os
import hmac
import hashlib
import base64
import json
import time
from typing import Dict, Any, List, Optional
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-prod")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def base64_url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, hashed: str) -> bool:
    parts = hashed.split(":")
    if len(parts) != 2:
        return False
    salt = bytes.fromhex(parts[0])
    key = bytes.fromhex(parts[1])
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return hmac.compare_digest(key, new_key)


class IdentityProvider:
    """Abstract interface for external identity providers (LDAP, OAuth2, SAML)"""
    def authenticate(self, username: str, credentials: str) -> bool:
        raise NotImplementedError()


class LocalIdentityProvider(IdentityProvider):
    """Local identity provider using predefined/local user credentials storage"""
    def __init__(self):
        # Username to hashed password dictionary
        self.users = {}

    def register_user(self, username: str, password: str):
        self.users[username] = hash_password(password)

    def authenticate(self, username: str, credentials: str) -> bool:
        hashed = self.users.get(username)
        if not hashed:
            return False
        return verify_password(credentials, hashed)


class AuthenticationService:
    """Enterprise Authentication Service for issuing JWT tokens, refreshing sessions and logout"""

    def __init__(self, provider: Optional[IdentityProvider] = None):
        self.provider = provider or LocalIdentityProvider()
        self.sessions = {} # refresh_token -> username

    def authenticate_user(self, username: str, credentials: str) -> Optional[Dict[str, Any]]:
        try:
            if self.provider.authenticate(username, credentials):
                logger.info("User authenticated")
                
                access_token = self.issue_access_token(username)
                refresh_token = self.issue_refresh_token(username)
                
                logger.info("Token issued")
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            else:
                logger.warning("Invalid credentials")
                return None
        except Exception as e:
            logger.error("Authentication failure")
            raise e

    def issue_access_token(self, username: str) -> str:
        payload = {
            "sub": username,
            "exp": time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        }
        return self._generate_jwt(payload)

    def issue_refresh_token(self, username: str) -> str:
        refresh_token = base64_url_encode(os.urandom(32))
        self.sessions[refresh_token] = {
            "username": username,
            "exp": time.time() + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
        }
        return refresh_token

    def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(refresh_token)
        if not session:
            logger.warning("Invalid refresh token")
            return None

        if session["exp"] < time.time():
            logger.warning("Expired token")
            self.sessions.pop(refresh_token, None)
            return None

        logger.info("Token refreshed")
        username = session["username"]
        new_access_token = self.issue_access_token(username)
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    def validate_access_token(self, token: str) -> Optional[str]:
        try:
            payload = self._verify_jwt(token)
            return payload.get("sub")
        except ValueError as e:
            logger.warning(f"Expired token / validation failed: {e}")
            logger.error("Token validation failure")
            return None

    def logout(self, refresh_token: str) -> bool:
        if refresh_token in self.sessions:
            self.sessions.pop(refresh_token)
            return True
        return False

    def _generate_jwt(self, payload: dict) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64_url_encode(json.dumps(header).encode('utf-8'))
        payload_b64 = base64_url_encode(json.dumps(payload).encode('utf-8'))
        
        signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
        sig_b64 = base64_url_encode(sig)
        
        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def _verify_jwt(self, token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        header_b64, payload_b64, sig_b64 = parts
        signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
        expected_sig_b64 = base64_url_encode(expected_sig)
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            raise ValueError("Invalid signature")
            
        payload = json.loads(base64_url_decode(payload_b64).decode('utf-8'))
        if "exp" in payload and payload["exp"] < time.time():
            raise ValueError("Expired token")
            
        return payload
