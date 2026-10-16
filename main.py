"""FastAPI statistics API with strict, single-origin CORS and response metadata."""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware

EMAIL = "23f2000363@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-v2r2tu.example.com"
INTEGER_RE = re.compile(r"^[+-]?[0-9]+$")


class RequestMetadataMiddleware:
    """Add request ID and elapsed-time headers to every HTTP response.

    This middleware intentionally wraps the CORS middleware, so preflight,
    rejected preflight, regular endpoint, 404, and error responses receive the
    same required metadata headers.
    """

    def __init__(self, app: Callable[..., Awaitable[Any]]) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        started = time.perf_counter()

        async def send_with_metadata(message: dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                elapsed = max(0.0, time.perf_counter() - started)
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in (b"x-request-id", b"x-process-time")
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                headers.append((b"x-process-time", f"{elapsed:.6f}".encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_metadata)


api = FastAPI(title="Statistics API", version="1.0.0")


@api.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "stats-cors-api", "status": "ok"}


@api.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/stats")
def get_stats(values: str = Query(..., description="Comma-separated base-10 integers")) -> dict[str, Any]:
    raw_parts = values.split(",")
    if not raw_parts or any(not part.strip() for part in raw_parts):
        raise HTTPException(status_code=400, detail="values must be a comma-separated list of integers")

    cleaned_parts = [part.strip() for part in raw_parts]
    if any(INTEGER_RE.fullmatch(part) is None for part in cleaned_parts):
        raise HTTPException(status_code=400, detail="values must contain only base-10 integers")

    numbers = [int(part, 10) for part in cleaned_parts]
    total = sum(numbers)
    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / len(numbers),
    }


# Only the assigned origin is allowed. No wildcard origins or credentials.
cors_app = CORSMiddleware(
    app=api,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Exam-Tag"],
    max_age=600,
)

# Keep metadata middleware outermost so it also decorates CORS preflight and
# rejected-preflight responses.
app = RequestMetadataMiddleware(cors_app)
