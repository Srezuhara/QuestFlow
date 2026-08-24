"""Minimal logging setup — the app had no logging configuration before this;
this is the first. A `logging.Filter` injects the current request's ID (from
`core/middleware.py`'s `ContextVar`) into every record, and the format string
includes it, so any future log line can be correlated back to the request
that produced it via the same `X-Request-ID` the client received.
"""

from __future__ import annotations

import logging

from app.core.middleware import get_request_id


class RequestIDLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIDLogFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
