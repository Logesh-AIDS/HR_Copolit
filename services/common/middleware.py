# services/common/middleware.py
import logging
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from services.common.config import settings
from services.common.redis_client import redis_cache

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Fixed-window rate limiting middleware backed by Redis.
    Bypasses health checks, live checks, and WebSockets to prevent interruptions.
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Bypass checks for WebSockets and system probes
        if "ws" in path or path in {"/health", "/ready", "/live", "/version", "/docs", "/openapi.json"}:
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        redis_client = redis_cache.get_client()
        key = f"rate_limit:{client_ip}"
        
        try:
            # Atomic increment
            count = redis_client.incr(key)
            if count == 1:
                # Set TTL window (60 seconds)
                redis_client.expire(key, 60)
                
            if count > settings.RATE_LIMIT_RPM:
                logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                            "details": {
                                "client_ip": client_ip,
                                "rpm_limit": settings.RATE_LIMIT_RPM
                            }
                        }
                    }
                )
        except Exception as e:
            # Fallback resiliency: Log failure and continue processing request if Redis is unavailable
            logger.error(f"Rate limiting failure (bypassed): {e}")
            
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware logging duration and metadata for all API transactions.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        # Process the request
        response = await call_next(request)
        
        duration = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code
        
        # Log transaction metrics (avoid flooding logs with health check successes)
        if path not in {"/health", "/ready", "/live"}:
            log_msg = f"{method} {path} completed with status {status_code} in {duration}ms"
            if status_code >= 500:
                logger.error(log_msg)
            elif status_code >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)
                
        return response
