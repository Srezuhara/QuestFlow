"""`X-Request-ID` — minted per request (or echoed if the client already sent
one), stored in a `ContextVar` so both the RFC 7807 exception handlers
(`core/errors.py`) and the logging filter (`core/logging_config.py`) can read
it without threading it through every call site, and echoed back on the
response header.
"""

from __future__ import annotations

from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from uuid_extensions import uuid7

REQUEST_ID_HEADER = "X-Request-ID"

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid7())
        token = _request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            _request_id_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
