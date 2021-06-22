import abc
from threading import Thread
from typing import Optional

from rosny.abstract import LoopStream


class ThreadStream(LoopStream, metaclass=abc.ABCMeta):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9,
                 daemon: bool = False):
        super().__init__(loop_rate=loop_rate, min_sleep=min_sleep, daemon=daemon)
        self._driver = None
        self._stopped = True

    def _start_driver(self):
        self._driver = Thread(target=self.work_loop,
                              name=self.name,
                              daemon=self.daemon)
        self.logger.info(f"Starting thread {self.name}")
        self._stopped = False
        self._driver.start()

    def _stop_driver(self):
        self._stopped = True

    def _join_driver(self, timeout):
        self._driver.join(timeout)
        if self._driver.is_alive():
            self.logger.error(f"Thread '{self._driver}' join timeout {timeout}")
        else:
            self._driver = None
            self._internal_state.clear_exit()

    def stopped(self) -> bool:
        return self._stopped
