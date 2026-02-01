import atexit
import datetime
import itertools
import logging
import os
import signal
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from typing import Callable, TextIO, cast

import psutil

__all__ = [
    "LauncherBase",
    "ProcessMeta",
    "defer_termination_signals",
    "restore_signal_mask",
    "exit_handler",
]

logger = logging.getLogger(__name__)


@dataclass
class ProcessMeta:
    proc: psutil.Popen
    log_file: TextIO


class LauncherBase(ABC):
    """
    Maintain the life cycle of the spawned processes.
    """

    procs: list[ProcessMeta | None]

    _lock: threading.Lock
    _log_counter: itertools.cycle
    _logging_interval: int

    def __init__(
        self,
        exit_timeout: float = 180,
        logging_interval: int = 60,
        *,
        # For testability,
        register_atexit: bool = True,
    ):
        self.procs = []
        self._logging_interval = logging_interval
        # log every 60 * 10s = 10 minutes
        self._log_counter = itertools.cycle(range(logging_interval))
        self._lock = threading.Lock()
        if register_atexit:
            atexit.register(exit_handler, self, exit_timeout, "Normal Exit signal received")

    def is_healthy(self) -> bool:
        return self._is_healthy()

    def _is_healthy(self, log_name="Process", offset=None) -> bool:
        """Check for all process, process is alive or process is None."""
        count = next(self._log_counter)
        with self._lock:
            for i, proc_meta in enumerate(self.procs):
                if proc_meta is None:
                    continue

                p = proc_meta.proc
                idx = "" if offset is None else f" {offset + i}"
                if p.poll() is not None:
                    logger.warning(
                        "[Launcher] %s%s pid=%d exited unexpectedly, exit code: %d",
                        log_name,
                        idx,
                        p.pid,
                        p.returncode,
                    )
                    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if proc_meta.log_file:
                        proc_meta.log_file.write(
                            f"{date_str} runner fail; only for report log to forge\n"
                        )
                    return False
                if count == 0:
                    logger.info(
                        "[Launcher] %s%s is running. pid=%d pgid=%d sid=%d",
                        log_name,
                        idx,
                        p.pid,
                        os.getpgid(p.pid),
                        os.getsid(p.pid),
                    )
        return True

    def all_alive(self) -> bool:
        with self._lock:
            # return False if procs is empty
            if not self.procs:
                return False
            # all([]) returns True
            return all(p is not None and p.proc.poll() is None for p in self.procs)

    def any_alive(self) -> bool:
        with self._lock:
            # any([]) returns False
            return any(p is not None and p.proc.poll() is None for p in self.procs)

    @abstractmethod
    def launch(self, *args, **kwargs) -> None:
        """Launch the processes and maintain their metadata in self.procs."""

    def kill_and_wait(self, timeout: float = 5, *args, **kwargs):
        with self._lock:
            proc_metas = [proc for proc in self.procs if proc is not None]
            kill_procs(proc_metas, timeout)

            # Clean status
            for idx in range(len(self.procs)):
                self.procs[idx] = None
            self._log_counter = itertools.cycle(range(self._logging_interval))

    def wait(self) -> list[int | None]:
        exit_codes: list[int | None] = [None] * len(self.procs)
        for i, proc_meta in enumerate(self.procs):
            if proc_meta is None:
                continue
            p = proc_meta.proc
            p.wait()
            exit_codes[i] = p.returncode
            logger.info("[Launcher] Process pid=%d exited with code %d", p.pid, p.returncode)
        # Clean status
        for idx in range(len(self.procs)):
            self.procs[idx] = None
        self._log_counter = itertools.cycle(range(self._logging_interval))

        return exit_codes


def kill_procs(proc_metas: list[ProcessMeta], timeout: float = 5):
    """Guarantee failed procs are killed and log files are closed."""

    # ! Scan all process that has the same pgid with self.procs. This is necessary
    # ! to avoid that when bash is killed by -9 SIGKILL, runner process become orphan
    # ! and its ppid=1 and not listed in curr_process.children(recursive=True)

    # Popen with start_new_session=True guarantees that p.pid == p.pgid
    child_pgids = [p.proc.pid for p in proc_metas]
    child_pgid_procs: list[psutil.Process] = []
    for proc in psutil.process_iter(["pid"]):
        try:
            if os.getpgid(proc.pid) in child_pgids:
                child_pgid_procs.append(proc)
        except (psutil.NoSuchProcess, ProcessLookupError):
            logger.info("[Launcher] Process %d already terminated, no need to wait", proc.pid)
            continue

    # ! a child process of nsys might spawn our base_runner process by setting new
    # ! pgid, so we need to reap its children, trying our best.
    # ! But if our base_runner process is already an orphan with new pgid,
    # ! there's no way to figure out that it's formerly a child of this launcher.
    all_children: list[psutil.Process] = [p.proc for p in proc_metas]
    for proc in child_pgid_procs:
        all_children.append(proc)
        all_children.extend(proc.children(recursive=True))

    # Send SIGTERM to all children
    need_to_wait: list[psutil.Process] = []
    for proc in set(all_children):
        logger.info("[Launcher] Send SIGTERM to child process %d", proc.pid)
        try:
            proc.terminate()
        except psutil.ZombieProcess:
            logger.warning("[Launcher] Child process %d is a zombie, reaping it", proc.pid)
            proc.wait()
        except psutil.NoSuchProcess:
            logger.info("[Launcher] Child process %d already terminated", proc.pid)
            continue
        except psutil.AccessDenied:
            logger.warning("[Launcher] Access denied to terminate child process %d", proc.pid)
            continue
        else:
            need_to_wait.append(proc)

    # In some region(like GCP), there are very flaky kernel syscall which might cause
    # process to be stuck in uninterruptible sleep state. If that happens, waiting for
    # maximum 5 min then exit.
    tolerance_extra_timeout = 300
    retry_sigkill_every = 30

    def kill_callback(p: psutil.Process):
        with suppress(Exception):
            p.kill()

    for tries in range(tolerance_extra_timeout // retry_sigkill_every + 1):
        # For the first try, we wait for the given timeout
        _timeout = timeout if tries == 0 else retry_sigkill_every

        need_to_wait = wait_for_procs(
            need_to_wait, kill_callback, "killing it with SIGKILL", _timeout
        )
        if not need_to_wait:
            break
    else:
        # After all retries, some processes are still alive, force exit
        for p in need_to_wait:
            logger.critical(
                "[Launcher] Child process %d didn't respond to SIGKILL after %d seconds!",
                p.pid,
                tolerance_extra_timeout,
            )
        logger.critical("[Launcher] Exiting launcher process forcefully!")
        os._exit(1)

    for proc in proc_metas:
        proc.log_file.close()

    logger.info("[Launcher] All processes & log_files are closed.")


def wait_for_procs(
    procs: list[psutil.Process],
    callback: Callable[[psutil.Process], None],
    callback_msg: str,
    timeout: float = 5,
) -> list[psutil.Process]:
    gone, alive = psutil.wait_procs(procs, timeout=timeout)
    for p in gone:
        p = cast(psutil.Popen, p)
        logger.info(
            "[Launcher] Child process %d terminated with exit code %d",
            p.pid,
            p.returncode,
        )
    for p in alive:
        logger.warning(
            "[Launcher] Child process %d did not terminate in time, %s",
            p.pid,
            callback_msg,
        )
        callback(p)

    return alive


ALL_TERM_SIGNALS = {
    signal.SIGABRT,
    signal.SIGBUS,
    signal.SIGFPE,
    signal.SIGILL,
    signal.SIGINT,
    signal.SIGKILL,
    signal.SIGPIPE,
    signal.SIGQUIT,
    signal.SIGSEGV,
    signal.SIGTERM,
    signal.SIGSYS,
}


@contextmanager
def defer_termination_signals():
    # Block these signals and save the old signal mask.
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, ALL_TERM_SIGNALS)
    try:
        yield
    finally:
        # Restore the original signal mask.
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)


def restore_signal_mask():
    """restore the signal mask that might block all termination signals"""
    signal.pthread_sigmask(signal.SIG_UNBLOCK, ALL_TERM_SIGNALS)


def exit_handler(launcher: LauncherBase, timeout: float = 180, msg: str = ""):
    with defer_termination_signals():
        logger.info("=" * 80)
        if msg:
            logger.info(msg)
        logger.info("[ExitHandler] Release resource, timeout=%d s", timeout)
        lg_procs = [lg_proc for lg_proc in launcher.procs if lg_proc is not None]
        kill_procs(lg_procs, timeout)
        logger.info("[ExitHandler] Resource released")
