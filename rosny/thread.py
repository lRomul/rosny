from threading import Thread
from typing import Optional

from rosny.abstract import BaseStream
from rosny.timing import LoopRateManager


class BaseThreadStream(BaseStream):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9):
        super().__init__()
        self._thread = None
        self._stopped = True
        self._rate_manager = LoopRateManager(loop_rate=loop_rate,
                                             min_sleep=min_sleep)

    def work(self):
        raise NotImplementedError

    def work_loop(self):
        try:
            while not self._stopped:
                self.work()
                self._rate_manager.timing()
        except BaseException as exception:
            self.on_catch_exception(exception)

    def on_catch_exception(self, exception: BaseException):
        self.logger.exception(exception)
        self._internal_state.set_exit()

    def _start_thread(self):
        self._thread = Thread(target=self.work_loop,
                              name=self.name,
                              daemon=True)
        self._stopped = False
        self._thread.start()

    def _join_thread(self, timeout):
        self._thread.join(timeout)
        if self._thread.is_alive():
            self.logger.error(
                f"Thread '{self._thread}' join timeout {timeout}"
            )
        else:
            self._thread = None
            self._internal_state.clear_exit()

    def start(self):
        self.logger.info("Starting stream")
        if self._stopped:
            if self._thread is None:
                if not self._compiled:
                    self.compile()

                self.on_start_begin()
                self._start_thread()
                self.on_start_end()
                self.logger.info("Stream started")
            else:
                self.logger.error("Stream stopped but not joined")
        else:
            self.logger.error("Stream is already started")

    def stop(self):
        if not self._stopped:
            self.on_stop_begin()
            self._stopped = True
            self.on_stop_end()
            self.logger.info("Stop stream")

    def wait(self, timeout: Optional[float] = None):
        self.logger.info(f"Stream start waiting with timeout {timeout}")
        self.on_wait_begin()
        self._internal_state.wait_exit(timeout=timeout)
        self.on_wait_end()
        if self._internal_state.exit_is_set():
            self.logger.info("Stream stop waiting, exit event is set")
        else:
            self.logger.info("Stream stop waiting, timeout exceeded")

    def join(self, timeout: Optional[float] = None):
        if self._thread is not None:
            self.on_join_begin()
            self._join_thread(timeout=timeout)
            self.on_join_end()
            self.logger.info("Stream joined")
        else:
            self.logger.error("Stream is already joined")
