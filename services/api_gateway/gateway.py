"""
Enterprise API Gateway — Single entry point for all ECIP services.
Provides JWT auth, rate limiting, circuit breaker, request logging, and health aggregation.
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx
import time

from ecip_core.common.logger import get_logger
from services.api_gateway.middleware.rate_limiter import RateLimiter
from services.api_gateway.middleware.circuit_breaker import CircuitBreakerRegistry
from services.api_gateway.middleware.auth_middleware import AuthMiddleware
from services.api_gateway.middleware.request_logger import RequestLogger

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Gateway configuration
# ------------------------------------------------------------------

RATE_LIMIT_CAPACITY = 60
RATE_LIMIT_REFILL = 1.0
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_COOLDOWN = 30.0

# Downstream services (for health aggregation)
DOWNSTREAM_SERVICES = {
    "ecip_api": "http://127.0.0.1:8000",
}

# Public paths that bypass authentication
AUTH_BYPASS_PATHS = [
    "/health",
    "/api/v1/health",
    "/gateway",
    "/docs",
    "/openapi.json",
    "/redoc",
]

# ------------------------------------------------------------------
# Middleware instances
# ------------------------------------------------------------------

rate_limiter = RateLimiter(capacity=RATE_LIMIT_CAPACITY, refill_rate=RATE_LIMIT_REFILL)
circuit_registry = CircuitBreakerRegistry(
    failure_threshold=CIRCUIT_FAILURE_THRESHOLD,
    cooldown_seconds=CIRCUIT_COOLDOWN,
)
auth_middleware = AuthMiddleware(bypass_paths=AUTH_BYPASS_PATHS)
request_logger = RequestLogger()

# ------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------

gateway = FastAPI(
    title="ECIP Enterprise API Gateway",
    version="1.0.0",
    description="Single entry point for all ECIP Enterprise services.",
)


@gateway.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Central middleware: logging, rate limiting, circuit breaker, auth."""
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method

    # 1. Request logging
    ctx = request_logger.start_request(method, path, client_ip)

    # 2. Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        request_logger.end_request(ctx, 429)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please slow down."},
            headers={"Retry-After": "1"},
        )

    # 3. JWT authentication (skip bypass paths)
    if not auth_middleware.should_bypass(path):
        auth_header = request.headers.get("Authorization")
        payload = auth_middleware.validate(auth_header)
        if payload is None:
            request_logger.end_request(ctx, 401)
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: invalid or missing token"},
            )

    # 4. Circuit breaker check
    cb = circuit_registry.get("ecip_api")
    if not cb.allow_request():
        request_logger.end_request(ctx, 503)
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable (circuit open)"},
        )

    # 5. Forward request
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            cb.record_failure()
        else:
            cb.record_success()
        request_logger.end_request(ctx, response.status_code)
        return response
    except Exception as e:
        cb.record_failure()
        request_logger.end_request(ctx, 500)
        logger.error("Routing failure")
        return JSONResponse(status_code=500, content={"detail": "Gateway error"})


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@gateway.get("/health", tags=["Gateway"])
async def health():
    """Aggregated health endpoint for all downstream services."""
    status = {"gateway": "healthy", "services": {}}

    for name, base_url in DOWNSTREAM_SERVICES.items():
        cb = circuit_registry.get(name)
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{base_url}/health")
                service_status = "healthy" if resp.status_code == 200 else "degraded"
        except Exception:
            service_status = "unavailable"

        status["services"][name] = {
            "status": service_status,
            "circuit": cb.state.value,
        }

    all_healthy = all(s["status"] == "healthy" for s in status["services"].values())
    return {
        **status,
        "overall": "healthy" if all_healthy else "degraded",
    }


@gateway.get("/gateway/circuit-breakers", tags=["Gateway"])
async def circuit_breaker_status():
    """Return the state of all circuit breakers."""
    return {"circuit_breakers": circuit_registry.status()}


@gateway.get("/gateway/rate-limit-info", tags=["Gateway"])
async def rate_limit_info():
    """Return rate limiter configuration."""
    return {
        "capacity": rate_limiter.capacity,
        "refill_rate_per_second": rate_limiter.refill_rate,
    }
