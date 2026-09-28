from __future__ import annotations

import threading

import pytest

import squarecloud.client


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Backoff never really sleeps in tests; the delays are recorded."""
    delays: list[float] = []

    def record(seconds: float, stop: threading.Event | None = None) -> None:
        delays.append(seconds)

    monkeypatch.setattr(squarecloud.client, '_sleep', record)
    return delays
