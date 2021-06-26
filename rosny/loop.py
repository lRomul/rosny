import abc
from typing import Optional, Union

from rosny.state import CommonState
from rosny.abstract import BaseStream
from rosny.timing import LoopRateManager
from rosny.signal import start_signals, stop_signals


class LoopStream(BaseStream, metaclass=abc.ABCMeta):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9,
                 daemon: bool = False):
        super().__init__()
        self.daemon = daemon
        self._driver = None
        self.rate_manager = LoopRateManager(loop_rate=loop_rate,
                                            min_sleep=min_sleep)

    @abc.abstractmethod
    def work(self):
        pass

    def work_loop(self):
        self.on_work_loop_begin()
        try:
            self.rate_manager.reset()
            while not self.stopped():
                self.work()
                self.rate_manager.timing()
        except (Exception, KeyboardInterrupt) as exception:
            self.on_catch_exception(exception)
        finally:
            self.on_work_loop_end()

    def on_catch_exception(self, exception: Union[Exception, KeyboardInterrupt]):
        self.logger.exception(exception)
        self.common_state.set_exit()

    def on_work_loop_begin(self):
        pass

    def on_work_loop_end(self):
        pass

    @abc.abstractmethod
    def _start_driver(self):
        pass

    @abc.abstractmethod
    def _stop_driver(self):
        pass

    @abc.abstractmethod
    def _join_driver(self, timeout):
        pass

    def compile(self,
                common_state: Optional[CommonState] = None,
                name: Optional[str] = None):
        self.on_compile_begin()
        super().compile(common_state=common_state, name=name)
        self.on_compile_end()

    def start(self):
        self.logger.info("Starting stream")
        if self.stopped():
            if self.joined():
                if not self.compiled():
                    self.compile()
                self.common_state.clear_exit()
                self.on_start_begin()
                self._start_driver()
                if self._handle_signals:
                    start_signals(self)
                self.on_start_end()
                self.logger.info("Stream started")
            else:
                self.logger.error("Stream stopped but not joined")
        else:
            self.logger.error("Stream is already started")

    def stop(self):
        self.logger.info("Stopping stream")
        if not self.stopped():
            self.on_stop_begin()
            self._stop_driver()
            if self._handle_signals:
                stop_signals(self)
            self.on_stop_end()
            self.logger.info("Stream stopped")
        else:
            self.logger.error("Stream is already stopped")

    def join(self, timeout: Optional[float] = None):
        self.logger.info("Joining stream")
        if not self.joined():
            self.on_join_begin()
            self._join_driver(timeout=timeout)
            self.on_join_end()
            self.logger.info("Stream joined")
        else:
            self.logger.error("Stream is already joined")

    def joined(self) -> bool:
        return self._driver is None
