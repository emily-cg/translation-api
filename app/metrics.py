from prometheus_client import Counter, Gauge, Histogram


translator_requests_total = Counter(
    "translator_requests_total",
    "Total number of HTTP requests",
    ["endpoint", "method", "status_code"],
)

translator_errors_total = Counter(
    "translator_errors_total",
    "Total number of translation errors",
    ["endpoint", "error_category"],
)

translator_request_latency_seconds = Histogram(
    "translator_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
)

translator_model_available = Gauge(
    "translator_model_available",
    "Whether the translation model is available",
)
