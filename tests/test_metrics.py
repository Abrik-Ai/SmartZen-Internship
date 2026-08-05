from unittest.mock import patch

from app.metrics import LatencyTracker, QueueDepthTracker, get_gpu_usage


def test_latency_tracker_reports_percentiles() -> None:
    tracker = LatencyTracker()
    # 0.001s .. 0.100s, evenly spread, in seconds
    for i in range(1, 101):
        tracker.record("/assistant/status", i / 1000)

    result = tracker.percentiles()["/assistant/status"]
    assert result["count"] == 100
    assert 49.0 <= result["p50_ms"] <= 51.0
    assert 94.0 <= result["p95_ms"] <= 96.0
    assert 98.0 <= result["p99_ms"] <= 100.0


def test_latency_tracker_keeps_routes_independent() -> None:
    tracker = LatencyTracker()
    tracker.record("/health", 0.001)
    tracker.record("/assistant/status", 0.5)

    result = tracker.percentiles()
    assert set(result.keys()) == {"/health", "/assistant/status"}
    assert result["/health"]["p50_ms"] < result["/assistant/status"]["p50_ms"]


def test_latency_tracker_caps_sample_count() -> None:
    tracker = LatencyTracker(max_samples=10)
    for i in range(50):
        tracker.record("/route", i / 1000)

    # internal list should never exceed the cap
    assert len(tracker._samples["/route"]) == 10


def test_route_with_no_samples_is_not_in_the_report() -> None:
    tracker = LatencyTracker()
    assert tracker.percentiles() == {}


def test_queue_depth_tracks_concurrent_slots() -> None:
    tracker = QueueDepthTracker()
    assert tracker.depth == 0

    with tracker.slot():
        assert tracker.depth == 1
        with tracker.slot():
            assert tracker.depth == 2
        assert tracker.depth == 1

    assert tracker.depth == 0


def test_queue_depth_releases_slot_even_if_the_body_raises() -> None:
    tracker = QueueDepthTracker()
    try:
        with tracker.slot():
            raise ValueError("boom")
    except ValueError:
        pass

    assert tracker.depth == 0


def test_gpu_usage_is_none_when_nvidia_smi_is_not_on_path() -> None:
    with patch("app.metrics.shutil.which", return_value=None):
        assert get_gpu_usage() is None


def test_gpu_usage_is_none_when_nvidia_smi_fails() -> None:
    import subprocess

    with (
        patch("app.metrics.shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch("app.metrics.subprocess.run", side_effect=subprocess.SubprocessError("nope")),
    ):
        assert get_gpu_usage() is None


def test_gpu_usage_parses_nvidia_smi_csv_output() -> None:
    fake_result = type(
        "FakeResult",
        (),
        {"stdout": "0, 42, 1024, 8192\n1, 10, 512, 8192\n"},
    )()

    with (
        patch("app.metrics.shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch("app.metrics.subprocess.run", return_value=fake_result),
    ):
        gpus = get_gpu_usage()

    assert gpus == [
        {"index": 0, "utilization_pct": 42.0, "memory_used_mb": 1024.0, "memory_total_mb": 8192.0},
        {"index": 1, "utilization_pct": 10.0, "memory_used_mb": 512.0, "memory_total_mb": 8192.0},
    ]
