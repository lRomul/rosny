import abc
from threading import Thread
from typing import Optional

from rosny.loop import LoopStream


class ThreadStream(LoopStream, metaclass=abc.ABCMeta):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9,
                 profile_interval: Optional[float] = None,
                 daemon: bool = False):
        super().__init__(loop_rate=loop_rate,
                         min_sleep=min_sleep,
                         profile_interval=profile_interval,
                         daemon=daemon)
        self._driver: Optional[Thread] = None
        self._stopped = True

    def _start_driver(self):
        self._driver = Thread(target=self.loop,
                              name=self.name,
                              daemon=self.daemon)
        self.logger.info(f"Starting thread {self.name}")
        self._stopped = False
        self._driver.start()

    def _stop_driver(self):
        self._stopped = True

    def _join_driver(self, timeout: Optional[float] = None):
        if self._driver is not None:
            self._driver.join(timeout)
            if self._driver.is_alive():
                self.logger.error(f"Thread '{self._driver}' join timeout {timeout}")
            else:
                self._driver = None

    def stopped(self) -> bool:
        return self._stopped
