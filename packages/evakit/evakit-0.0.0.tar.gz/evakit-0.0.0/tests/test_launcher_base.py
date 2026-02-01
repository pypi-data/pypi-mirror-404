import io
import signal

from evakit import launcher_base
from evakit.launcher_base import (
    LauncherBase,
    ProcessMeta,
    defer_termination_signals,
    exit_handler,
    kill_procs,
    restore_signal_mask,
)


# -----------------------------
# Dummy process and launcher
# -----------------------------
class DummyProcess:
    def __init__(self, pid=1234, alive=True):
        self.pid = pid
        self.returncode = 0
        self.alive = alive
        self._terminated = False
        self._killed = False

    def poll(self):
        return None if self.alive else 1

    def wait(self, timeout=None):
        self.alive = False
        return self.returncode

    def terminate(self):
        self._terminated = True
        self.alive = False

    def kill(self):
        self._killed = True
        self.alive = False

    def children(self, recursive=True):
        return []

    def __repr__(self):
        return f"<DummyProcess pid={self.pid}>"


class DummyLauncher(LauncherBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, register_atexit=False)

    def launch(self):
        pass


# -----------------------------
# kill_procs tests
# -----------------------------
def test_kill_procs_normal(mocker):
    p1 = DummyProcess(pid=1001)
    p2 = DummyProcess(pid=1002)
    meta1 = ProcessMeta(proc=p1, log_file=io.StringIO())
    meta2 = ProcessMeta(proc=p2, log_file=io.StringIO())

    # Patch psutil internals so we don’t touch real system processes
    mocker.patch("psutil.process_iter", return_value=[])
    mocker.patch("psutil.wait_procs", return_value=([], []))

    kill_procs([meta1, meta2], timeout=1)

    # Should have terminated and closed logs
    assert meta1.log_file.closed
    assert meta2.log_file.closed


def test_kill_procs_with_zombie(mocker):
    zombie = DummyProcess(pid=2001)
    meta = ProcessMeta(proc=zombie, log_file=io.StringIO())

    mocker.patch("psutil.process_iter", return_value=[zombie])
    mocker.patch("psutil.wait_procs", return_value=([], []))
    mocker.patch("os.getpgid", return_value=2001)

    kill_procs([meta], timeout=0.1)
    assert meta.log_file.closed


# -----------------------------
# Signal mask tests
# -----------------------------
def test_defer_termination_signals(monkeypatch):
    calls = []

    def fake_sigmask(*args):
        calls.append(args)
        return "oldmask"

    monkeypatch.setattr(signal, "pthread_sigmask", fake_sigmask)

    with defer_termination_signals():
        pass

    assert len(calls) == 2


def test_restore_signal_mask(monkeypatch):
    calls = []

    def fake_sigmask(*args):
        calls.append(args)
        return "oldmask"

    monkeypatch.setattr(signal, "pthread_sigmask", fake_sigmask)

    restore_signal_mask()
    assert len(calls) == 1
    assert calls[0][0] == signal.SIG_UNBLOCK


def test_launcher_is_healthy(mocker):
    p = DummyProcess(pid=123)
    log = io.StringIO()
    dummy_launcher = DummyLauncher()
    dummy_launcher.procs = [ProcessMeta(proc=p, log_file=log)]

    mocker.patch("os.getpgid", return_value=123)
    mocker.patch("os.getsid", return_value=123)

    assert dummy_launcher.is_healthy() is True


def test_launcher_detects_dead_process():
    p = DummyProcess(pid=123, alive=False)
    log = io.StringIO()
    dummy_launcher = DummyLauncher()
    dummy_launcher.procs = [ProcessMeta(proc=p, log_file=log)]
    assert dummy_launcher.is_healthy() is False
    log.seek(0)
    assert "runner fail" in log.read()


def test_exit_handler(monkeypatch, mocker):
    dummy_launcher = DummyLauncher()
    dummy_launcher.procs = []

    monkeypatch.setattr(
        launcher_base.signal,
        "pthread_sigmask",
        lambda *a, **k: None,
    )

    killed = mocker.patch("evakit.launcher_base.kill_procs")

    exit_handler(dummy_launcher, timeout=1, msg="cleanup")

    killed.assert_called_once()
