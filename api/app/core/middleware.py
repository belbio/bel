# Standard Library
import re
import time

# Local Imports
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


@logger.catch
class StatsMiddleware(BaseHTTPMiddleware):
    """Get duration of request"""

    async def dispatch(self, request, call_next):

        url = str(request.url)
        method = str(request.method)
        t0 = time.time()

        response = await call_next(request)

        url = url.rstrip("/")
        route_name = url.split("/")[-1]

        # logger.info("Skipping status/metrics", url=url, route_name=route_name)

        if method == "OPTIONS" or route_name in ["status", "metrics", "ping"]:
            return response
        else:
            t1 = time.time()

            duration = f"{(t1 - t0) * 1000:.0f}"

            logger.opt(exception=True).info(
                "Request Metrics {duration_ms} ms, status_code: {status_code}  {method} {url}",
                # "Request Metrics {duration_ms} ms, status_code: {status_code}",
                duration_ms=duration,
                status_code=response.status_code,
                method=method,
                url=url,
            )

            return response
