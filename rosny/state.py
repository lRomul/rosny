import threading
from typing import Optional


class State:
    def __init__(self):
        self._exit_event = threading.Event()

    def set_exit(self):
        self._exit_event.set()

    def clear_exit(self):
        self._exit_event.clear()

    def wait_exit(self, timeout: Optional[float] = None):
        self._exit_event.wait(timeout=timeout)

    def exit_is_set(self) -> bool:
        return self._exit_event.is_set()
