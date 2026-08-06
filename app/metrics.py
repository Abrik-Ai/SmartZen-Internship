"""Backs GET /assistant/metrics.

Everything here is in-memory and process-local — same caveat as
app/rate_limit.py: fine for a single uvicorn worker, but multiple
workers/replicas would each report their own slice, not a combined view.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from collections import defaultdict

MAX_SAMPLES_PER_ROUTE = 1000  # bounded so this can't grow forever
GPU_QUERY_TIMEOUT_SECONDS = 2.0


class LatencyTracker:
    """Keeps the last `max_samples` request durations per route and reports
    p50/p95/p99 from them."""

    def __init__(
        self,
        max_samples: int = MAX_SAMPLES_PER_ROUTE,
    ) -> None:
        self._max_samples = max_samples
        self._samples: dict[str, list[float]] = defaultdict(list)

    def record(self, route: str, duration_seconds: float) -> None:
        samples = self._samples[route]
        samples.append(duration_seconds)
        if len(samples) > self._max_samples:
            del samples[: len(samples) - self._max_samples]

    def percentiles(self) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for route, samples in self._samples.items():
            if not samples:
                continue
            ordered = sorted(samples)
            result[route] = {
                "p50_ms": round(_percentile(ordered, 50) * 1000, 2),
                "p95_ms": round(_percentile(ordered, 95) * 1000, 2),
                "p99_ms": round(_percentile(ordered, 99) * 1000, 2),
                "count": len(ordered),
            }
        return result


def _percentile(sorted_samples: list[float], pct: float) -> float:
    """Linear-interpolation percentile (the same method numpy.percentile
    defaults to), no numpy dependency needed for this."""
    if len(sorted_samples) == 1:
        return sorted_samples[0]
    rank = (len(sorted_samples) - 1) * (pct / 100)
    floor_i, ceil_i = math.floor(rank), math.ceil(rank)
    if floor_i == ceil_i:
        return sorted_samples[int(rank)]
    lower = sorted_samples[floor_i] * (ceil_i - rank)
    upper = sorted_samples[ceil_i] * (rank - floor_i)
    return lower + upper


class QueueDepthTracker:
    """Counts how many chat generations are in flight right now.

    Best-effort, not a hard admission-control lock: there's a small window
    between a caller checking `depth` and actually acquiring a slot where a
    burst of concurrent requests could all see room. Good enough for
    reporting + graceful degradation; not a substitute for a real semaphore
    if this ever needs to be exact.
    """

    def __init__(self) -> None:
        self._depth = 0

    @property
    def depth(self) -> int:
        return self._depth

    def slot(self) -> _QueueSlot:
        return _QueueSlot(self)


class _QueueSlot:
    def __init__(self, tracker: QueueDepthTracker) -> None:
        self._tracker = tracker

    def __enter__(self) -> _QueueSlot:
        self._tracker._depth += 1
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._tracker._depth -= 1


def get_gpu_usage() -> list[dict[str, float]] | None:
    """Best-effort GPU utilization via `nvidia-smi`.

    Returns None (never raises) when there's no GPU, no driver, the binary
    isn't on PATH, or the query fails for any reason — GPU usage is
    diagnostic, and its absence should never break the metrics endpoint.
    """
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return None

    try:
        result = subprocess.run(  # noqa: S603
            [
                nvidia_smi,
                "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=GPU_QUERY_TIMEOUT_SECONDS,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None

    gpus: list[dict[str, float]] = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            continue
        index, util_pct, mem_used_mb, mem_total_mb = parts
        try:
            gpus.append(
                {
                    "index": int(index),
                    "utilization_pct": float(util_pct),
                    "memory_used_mb": float(mem_used_mb),
                    "memory_total_mb": float(mem_total_mb),
                }
            )
        except ValueError:
            continue
    return gpus


latency_tracker = LatencyTracker()
queue_depth_tracker = QueueDepthTracker()


def record_latency(route: str, duration_seconds: float) -> None:
    latency_tracker.record(route, duration_seconds)


def get_metrics_snapshot() -> dict[str, object]:
    return {
        "latency": latency_tracker.percentiles(),
        "queue_depth": queue_depth_tracker.depth,
        "gpu": get_gpu_usage(),
    }