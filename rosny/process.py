from typing import Optional, Union
from multiprocessing import Process, Value

from rosny.abstract import BaseStream
from rosny.timing import LoopRateManager


class ProcessStream(BaseStream):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9):
        super().__init__()
        self._loop_rate = loop_rate
        self._min_sleep = min_sleep
        self._process = None
        self._stopped = Value('i', 1)
        self.rate_manager = LoopRateManager(loop_rate=self._loop_rate,
                                            min_sleep=self._min_sleep)

    def work(self):
        raise NotImplementedError

    def work_loop(self):
        try:
            self.rate_manager.reset()
            while not self.stopped():
                self.work()
                self.rate_manager.timing()
        except (Exception, KeyboardInterrupt) as exception:
            self.on_catch_exception(exception)

    def on_catch_exception(self, exception: Union[Exception, KeyboardInterrupt]):
        self.logger.exception(exception)
        self._internal_state.set_exit()

    def _start_process(self):
        self._process = Process(target=self.work_loop,
                                name=self.name,
                                daemon=True)
        self._stopped.value = 0
        self._process.start()

    def _join_process(self, timeout):
        self._process.join(timeout)
        if self._process.is_alive():
            self.logger.error(f"Process '{self._process}' join timeout {timeout}")
        else:
            self._process = None
            self._internal_state.clear_exit()

    def start(self):
        self.logger.info("Starting stream")
        if self.stopped():
            if self.joined():
                self.on_start_begin()
                self._start_process()
                self.on_start_end()
                self.logger.info("Stream started")
            else:
                self.logger.error("Stream stopped but not joined")
        else:
            self.logger.error("Stream is already started")

    def stop(self):
        self.logger.info("Stopping stream")
        if not self._stopped.value:
            self.on_stop_begin()
            self._stopped.value = True
            self.on_stop_end()
            self.logger.info("Stream stopped")
        else:
            self.logger.error("Stream is already stopped")

    def join(self, timeout: Optional[float] = None):
        self.logger.info("Joining stream")
        if not self.joined():
            self.on_join_begin()
            self._join_process(timeout=timeout)
            self.on_join_end()
            self.logger.info("Stream joined")
        else:
            self.logger.error("Stream is already joined")

    def stopped(self) -> bool:
        return self._stopped.value

    def joined(self) -> bool:
        return self._process is None
