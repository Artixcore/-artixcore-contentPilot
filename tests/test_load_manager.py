"""Tests for core.load_manager."""

import threading
import time

import pytest

from core.errors import LoadLimitError
from core.load_manager import reset_load_manager, with_load_slot


@pytest.fixture(autouse=True)
def clean_load():
    reset_load_manager()
    yield
    reset_load_manager()


def test_limits_concurrent_jobs(monkeypatch):
    monkeypatch.setenv("MAX_CONCURRENT_AI_REQUESTS", "1")
    reset_load_manager()
    import importlib
    import core.load_manager as lm

    importlib.reload(lm)
    lm.reset_load_manager()

    started = threading.Event()
    release = threading.Event()

    def slow():
        started.set()
        release.wait(timeout=2)

    t = threading.Thread(target=lambda: lm.with_load_slot("ai")(slow)())
    # Use context manager properly
    with lm.with_load_slot("ai"):
        started_inner = threading.Event()

        def inner():
            started_inner.set()
            time.sleep(0.2)

        thread = threading.Thread(
            target=lambda: lm.with_load_slot("ai")(inner)()
        )
        thread.start()
        started_inner.wait(timeout=1)
        with pytest.raises(LoadLimitError):
            with lm.with_load_slot("ai", timeout=0.05):
                pass
        thread.join(timeout=2)


def test_returns_overload_message():
    err = LoadLimitError()
    assert "many tasks" in err.message.lower()
