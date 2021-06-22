import abc
from typing import Optional
from multiprocessing import Process, Value

from rosny.abstract import LoopStream


class ProcessStream(LoopStream, metaclass=abc.ABCMeta):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9,
                 daemon: bool = False):
        super().__init__(loop_rate=loop_rate, min_sleep=min_sleep, daemon=daemon)
        self._driver = None
        self._stopped = Value('i', 1)

    def _start_driver(self):
        self._driver = Process(target=self.work_loop,
                               name=self.name,
                               daemon=self.daemon)
        self.logger.info(f"Starting process {self.name}")
        self._stopped.value = 0
        self._driver.start()

    def _stop_driver(self):
        self._stopped.value = 1

    def _join_driver(self, timeout):
        self._driver.join(timeout)
        if self._driver.is_alive():
            self.logger.error(f"Process '{self._driver}' join timeout {timeout}")
        else:
            self._driver = None
            self._internal_state.clear_exit()

    def stopped(self) -> bool:
        return self._stopped.value
