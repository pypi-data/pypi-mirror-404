import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from anti_sentinel.services.metrics import MetricsService

class SentinelMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate time taken
        process_time = (time.time() - start_time) * 1000 # Convert to ms
        
        # Log to DB (Fire and forget style)
        # In a huge production app, you'd use a background queue here.
        metrics = MetricsService.get_instance()
        await metrics.log_request(
            endpoint=request.url.path,
            method=request.method,
            status=response.status_code,
            latency=process_time
        )
        
        return response