import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server

    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False

    class _MockMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, amount=1):
            pass

        def dec(self, amount=1):
            pass

        def set(self, value):
            pass

        def observe(self, amount):
            pass

        def time(self):
            return self

        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    Counter = _MockMetric  # type: ignore
    Gauge = _MockMetric  # type: ignore
    Histogram = _MockMetric  # type: ignore

    def start_http_server(port: int, addr: str = "", registry: Any = None):
        logger.warning("prometheus-client not installed. Metrics server will not start.")


TASKS_SUBMITTED = Counter(
    "vtasks_tasks_submitted_total",
    "Total number of tasks submitted",
    ["task_name", "queue"],
)

TASKS_PROCESSED = Counter(
    "vtasks_tasks_processed_total",
    "Total number of tasks processed",
    ["task_name", "queue", "status"],
)

TASK_DURATION = Histogram(
    "vtasks_task_duration_seconds",
    "Task execution time in seconds",
    ["task_name", "queue"],
)

ACTIVE_TASKS = Gauge(
    "vtasks_active_tasks",
    "Number of tasks currently being processed",
    ["queue"],
)

QUEUE_DEPTH = Gauge(
    "vtasks_queue_depth",
    "Approximate number of tasks waiting in the queue",
    ["queue"],
)
