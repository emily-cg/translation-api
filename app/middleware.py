import time
import uuid

from fastapi import Request, Response

from app.metrics import (
    translator_request_latency_seconds,
    translator_requests_total,
)


async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    if endpoint == "/metrics":
        return await call_next(request)
    method = request.method
    start = time.perf_counter()
    response = await call_next(request)
    latency = time.perf_counter() - start
    translator_request_latency_seconds.labels(endpoint=endpoint).observe(latency)
    translator_requests_total.labels(
        endpoint=endpoint,
        method=method,
        status_code=str(response.status_code),
    ).inc()
    return response
