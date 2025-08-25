"""Metrics middleware for tracking response times and errors."""
import time
import asyncio
from typing import Callable, Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import deque
from datetime import datetime, timedelta

from ..telemetry.alerts import maybe_alert, AlertThresholds


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking metrics and triggering alerts."""
    
    def __init__(self, app):
        super().__init__(app)
        # Rolling windows for metrics (last 100 requests)
        self.response_times = deque(maxlen=100)
        self.status_codes = deque(maxlen=100)
        self.last_alert_check = datetime.utcnow()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Track metrics
            self.response_times.append(elapsed_ms)
            self.status_codes.append(response.status_code)
            
            # Add metrics headers
            response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"
            
            # Check for alerts periodically (every 10 seconds)
            if datetime.utcnow() - self.last_alert_check > timedelta(seconds=10):
                await self._check_alerts(request.url.path)
                self.last_alert_check = datetime.utcnow()
            
            return response
            
        except Exception as e:
            # Track error
            elapsed_ms = (time.time() - start_time) * 1000
            self.response_times.append(elapsed_ms)
            self.status_codes.append(500)
            raise
    
    async def _check_alerts(self, route: str):
        """Check metrics and trigger alerts if needed."""
        if not self.response_times or not self.status_codes:
            return
        
        # Calculate average latency
        avg_latency = sum(self.response_times) / len(self.response_times)
        
        # Calculate error rate
        error_count = sum(1 for code in self.status_codes if code >= 500)
        error_rate = error_count / len(self.status_codes)
        
        # Check latency threshold
        if avg_latency > AlertThresholds.LATENCY_MS:
            await maybe_alert(
                metric="latency_ms",
                value=avg_latency,
                threshold=AlertThresholds.LATENCY_MS,
                context={"route": route, "sample_size": len(self.response_times)}
            )
        
        # Check error rate threshold
        if error_rate > AlertThresholds.ERROR_RATE:
            await maybe_alert(
                metric="error_rate",
                value=error_rate,
                threshold=AlertThresholds.ERROR_RATE,
                context={"route": route, "errors": error_count, "total": len(self.status_codes)}
            )