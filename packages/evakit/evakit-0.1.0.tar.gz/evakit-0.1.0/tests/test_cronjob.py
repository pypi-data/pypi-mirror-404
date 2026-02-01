import threading
import time

import pytest

from evakit.cronjob import CronJob


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    # Ensure logs captured for assertion
    caplog.set_level("INFO")
    yield


def test_cronjob_executes_repeatedly():
    """CronJob should repeatedly execute the target until stopped."""
    counter = {"calls": 0}

    def task():
        counter["calls"] += 1

    job = CronJob(name="t1", task=task, interval=0.05)
    job.start()
    time.sleep(0.2)  # let a few cycles run
    job.stop()
    job.join(timeout=1)

    assert counter["calls"] >= 2
    assert not job.is_alive()


def test_cronjob_stop_sets_event():
    """Stop should set the internal event and allow run() to exit."""
    evt = threading.Event()

    def task():
        evt.set()  # signal we entered once

    job = CronJob(name="t2", task=task, interval=0.1)
    job.start()
    evt.wait(timeout=1)
    job.stop()
    job.join(timeout=1)

    assert job._stop_event.is_set()
    assert not job.is_alive()


def test_cronjob_handles_exceptions(caplog):
    """Exceptions in the task should be logged but not crash the thread."""

    def bad_task():
        raise RuntimeError("boom")

    job = CronJob(name="t3", task=bad_task, interval=0.05)
    job.start()
    time.sleep(0.1)
    job.stop()
    job.join(timeout=1)

    # Verify exception logged
    assert any("Exception: boom" in m for m in caplog.messages)


def test_cronjob_respects_interval():
    """CronJob should approximately honor the interval between task calls."""
    timestamps = []

    def task():
        timestamps.append(time.perf_counter())

    job = CronJob(name="t4", task=task, interval=0.05)
    job.start()
    time.sleep(0.16)
    job.stop()
    job.join(timeout=1)

    # Compute time gaps between consecutive calls
    diffs = [t2 - t1 for t1, t2 in zip(timestamps, timestamps[1:])]
    # Expect roughly >= 0.04s intervals (some jitter allowed)
    assert all(d >= 0.04 for d in diffs)
    assert not job.is_alive()
