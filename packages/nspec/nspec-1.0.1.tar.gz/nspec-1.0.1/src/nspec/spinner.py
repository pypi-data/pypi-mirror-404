"""Simple spinner for long-running operations."""

import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager


class Spinner:
    """A simple terminal spinner."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Working"):
        self.message = message
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _animate(self) -> None:
        idx = 0
        while not self._stop.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            sys.stderr.write(f"\r{frame} {self.message}...")
            sys.stderr.flush()
            idx += 1
            time.sleep(0.08)

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stderr.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stderr.flush()


@contextmanager
def spinner(message: str = "Working") -> Iterator[None]:
    """Context manager for showing a spinner."""
    s = Spinner(message)
    s.start()
    try:
        yield
    finally:
        s.stop()
