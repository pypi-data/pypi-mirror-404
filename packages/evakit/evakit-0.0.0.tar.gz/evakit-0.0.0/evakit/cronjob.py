import logging
import threading
from typing import Any, Callable

__all__ = ["CronJob"]

logger = logging.getLogger(__name__)


class CronJob(threading.Thread):
    interval: float | int

    _stop_event: threading.Event

    _target: Callable[..., Any]
    _args: tuple[Any, ...]
    _kwargs: dict[str, Any]

    def __init__(
        self,
        name: str,
        task: Callable,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        *,
        interval: float | int = 60,
        daemon: bool | None = True,
    ):
        super().__init__(
            target=task,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon,
        )
        self.interval_sec = interval
        self._stop_event = threading.Event()

    def run(self):
        logger.info("[CronJob %s] Started with interval %ss", self.name, self.interval_sec)
        while not self._stop_event.is_set():
            try:
                self._target(*self._args, **self._kwargs)
            except Exception as e:
                logger.exception("[CronJob %s] Exception: %s", self.name, e)
            # Wait with early exit if stopped
            if self._stop_event.wait(self.interval_sec):
                break

    def stop(self):
        self._stop_event.set()
        logger.info("[CronJob %s] Stopped", self.name)
