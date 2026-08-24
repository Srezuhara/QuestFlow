"""RFC 7807 (`application/problem+json`) exception handlers.

`detail` keeps its exact current value and shape (D9-6, PHASE_8_9_PLAN.md
§9.6) — including the list-of-error-objects form FastAPI's default
`RequestValidationError` handler produces for 422s. Every existing test and
the frontend's `ApiError` read `detail`; this only *adds* `type`/`title`/
`status`/`request_id` alongside it, so no existing behaviour changes.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (  # type: ignore[attr-defined]
    is_body_allowed_for_status_code,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.middleware import get_request_id

PROBLEM_CONTENT_TYPE = "application/problem+json"

# RFC 7807 has no registered `type` URIs for us to point at — these are
# stable, human-readable identifiers scoped to this API, not dereferenceable
# links, which RFC 7807 explicitly allows ("SHOULD... when dereferenced,
# provide human-readable documentation" — not a hard requirement).
_TITLE_BY_STATUS: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "Bad Request",
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not Found",
    status.HTTP_409_CONFLICT: "Conflict",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "Unprocessable Content",
}


def _problem_response(*, status_code: int, detail: object) -> JSONResponse:
    title = _TITLE_BY_STATUS.get(status_code, "Error")
    body = {
        "type": f"about:blank#{status_code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "request_id": get_request_id(),
    }
    return JSONResponse(status_code=status_code, content=body, media_type=PROBLEM_CONTENT_TYPE)


async def _handle_http_exception(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, HTTPException)
    # Mirrors FastAPI's own default handler: a 204/304 (or any status that
    # forbids a body) gets no body at all, problem+json or otherwise.
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=exc.headers)
    response = _problem_response(status_code=exc.status_code, detail=exc.detail)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return _problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=jsonable_encoder(exc.errors()),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
