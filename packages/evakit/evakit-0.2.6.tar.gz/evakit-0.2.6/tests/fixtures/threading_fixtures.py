import inspect
import random
import threading
import time
from concurrent import futures as cf
from dataclasses import dataclass, field
from typing import Any, Callable

import pytest

__all__ = ["thread_runner", "ThreadOutcome", "declares_param"]


@dataclass
class ThreadOutcome:
    started: threading.Event = field(default_factory=threading.Event)
    ended: threading.Event = field(default_factory=threading.Event)
    start_time: float = 0.0
    end_time: float = 0.0
    result: Any | None = None
    exc: BaseException | None = None


def declares_param(func, name="tid_") -> bool:
    try:
        sig = inspect.signature(func, follow_wrapped=True)
    except (TypeError, ValueError):
        return False
    p = sig.parameters.get(name)
    return p is not None and p.kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    )


@pytest.fixture
def thread_runner():
    """
    Run a target callable concurrently in N threads and collect outcomes.
    Returns:
        (outcomes, had_exception)
          - outcomes[i].result or outcomes[i].exc for each thread
          - had_exception: True if any thread raised or timed out
    Notes:
      - Cancels unfinished work when the first exception happens (if enabled).
      - Use with pytest-timeout for whole-test safety.
    """

    def run(
        n: int,
        target: Callable[..., Any],
        *args,
        timeout: float = 5.0,
        random_sleep_before_start: float = 0.0,
        cancel_on_first_exception: bool = True,
        **kwargs,
    ) -> tuple[list[ThreadOutcome], bool]:
        def _worker(outcome: ThreadOutcome, *, tid: int):
            if random_sleep_before_start > 0:
                time.sleep(random.uniform(0, random_sleep_before_start))
            outcome.start_time = time.perf_counter()
            outcome.started.set()
            if declares_param(target, "tid_"):
                kwargs["tid_"] = tid
            result = target(*args, **kwargs)
            outcome.result = result
            outcome.end_time = time.perf_counter()
            outcome.ended.set()

        with cf.ThreadPoolExecutor(max_workers=n, thread_name_prefix="pytest-thread") as ex:
            outcomes = [ThreadOutcome() for _ in range(n)]
            futures = [ex.submit(_worker, outcome, tid=idx) for idx, outcome in enumerate(outcomes)]
            if cancel_on_first_exception:
                cf.wait(futures, timeout=timeout, return_when=cf.FIRST_EXCEPTION)
            else:
                cf.wait(futures, timeout=timeout)
            had_exc = False
            for i, fut in enumerate(futures):
                if not fut.done():
                    fut.cancel()
                    outcomes[i].exc = TimeoutError("thread timed out")
                    outcomes[i].ended.clear()
                    outcomes[i].end_time = time.perf_counter()
                    had_exc = True
                    continue
                try:
                    fut.result()
                    assert outcomes[i].ended.is_set()
                except BaseException as e:  # noqa: BLE001
                    outcomes[i].exc = e
                    outcomes[i].ended.clear()
                    outcomes[i].end_time = time.perf_counter()
                    had_exc = True
        return outcomes, had_exc

    return run
