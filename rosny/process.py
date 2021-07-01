import abc
from typing import Optional
from multiprocessing import Process, Value

from rosny.loop import LoopStream
from rosny.utils import setup_logger


class ProcessStream(LoopStream, metaclass=abc.ABCMeta):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9,
                 profile_interval: Optional[float] = None,
                 daemon: bool = False):
        super().__init__(loop_rate=loop_rate,
                         min_sleep=min_sleep,
                         profile_interval=profile_interval,
                         daemon=daemon)
        self._driver: Optional[Process] = None
        self._stopped = Value('i', 1)

    def work_loop(self):
        self.logger = setup_logger(self.name)  # necessary for spawn and forkserver
        super().work_loop()

    def _start_driver(self):
        self._driver = Process(target=self.work_loop,
                               name=self.name,
                               daemon=self.daemon)
        self.logger.info(f"Starting process {self.name}")
        self._stopped.value = 0
        self._driver.start()

    def _stop_driver(self):
        self._stopped.value = 1

    def _join_driver(self, timeout: Optional[float] = None):
        if self._driver is not None:
            self._driver.join(timeout)
            if self._driver.is_alive():
                self.logger.error(f"Process '{self._driver}' join timeout {timeout}")
            else:
                self._driver = None
                self.common_state.clear_exit()

    def stopped(self) -> bool:
        return self._stopped.value
