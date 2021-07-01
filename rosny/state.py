from typing import Optional
from multiprocessing import Event, Manager


class CommonState:
    def __init__(self):
        self._manager: Optional[Manager] = Manager()
        self.profile_stats: dict = self._manager.dict()
        self._exit_event = Event()

    def set_exit(self):
        self._exit_event.set()

    def clear_exit(self):
        self._exit_event.clear()

    def wait_exit(self, timeout: Optional[float] = None):
        self._exit_event.wait(timeout=timeout)

    def exit_is_set(self) -> bool:
        return self._exit_event.is_set()

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        del state["_manager"]
        return state

    def __setstate__(self, state: dict):
        self.__dict__.update(state)
        self._manager = None
