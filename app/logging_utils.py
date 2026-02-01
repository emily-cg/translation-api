import json
import logging
import time

from typing import Dict, Any


logger = logging.getLogger("app.translate")


def log_translate(event: str, *, level: str = "info", **fields) -> None:
    payload = {"event": event, **fields}
    message = json.dumps(payload)

    if level == "exception":
        logger.exception(message)
        return

    logger.info(message)


class TranslateLogSpan:
    def __init__(self, base_fields: Dict[str, Any]):
        self.base_fields = base_fields
        self._start = None

    def __enter__(self) -> "TranslateLogSpan":
        self._start = time.perf_counter()
        log_translate("translate_start", **self.base_fields, status_code=0)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def _latency_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)

    def success(self, status_code: int) -> int:
        latency_ms = self._latency_ms()
        log_translate(
            "translate_success",
            **self.base_fields,
            latency_ms=latency_ms,
            status_code=status_code,
        )
        return latency_ms

    def failure(self, status_code: int, error_category: str, level: str = "info") -> int:
        latency_ms = self._latency_ms()
        log_translate(
            "translate_failure",
            level=level,
            **self.base_fields,
            latency_ms=latency_ms,
            status_code=status_code,
            error_category=error_category,
        )
        return latency_ms
