import abc
from typing import Optional, Union, Any

from rosny.state import CommonState
from rosny.abstract import BaseNode
from rosny.timing import LoopRateManager, Profiler


class LoopNode(BaseNode, metaclass=abc.ABCMeta):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9,
                 profile_interval: Optional[float] = None,
                 daemon: bool = False):
        super().__init__()
        self.daemon = daemon
        self._driver: Optional[Any] = None
        self.rate_manager = LoopRateManager(loop_rate=loop_rate,
                                            min_sleep=min_sleep)
        self.profiler = Profiler(node=self, interval=profile_interval)

    @abc.abstractmethod
    def work(self):
        pass

    def loop(self):
        try:
            self.on_loop_begin()
            self.rate_manager.reset()
            self.profiler.reset(self)
            while not self.stopped():
                self.work()
                self.rate_manager.timing()
                self.profiler.profile()
        except (Exception, KeyboardInterrupt) as exception:
            self.on_catch_exception(exception)
        finally:
            self.on_loop_end()

    def on_catch_exception(self, exception: Union[Exception, KeyboardInterrupt]):
        self.logger.exception(exception)
        self.common_state.set_exit()

    def on_loop_begin(self):
        pass

    def on_loop_end(self):
        pass

    @abc.abstractmethod
    def _start_driver(self):
        pass

    @abc.abstractmethod
    def _stop_driver(self):
        pass

    @abc.abstractmethod
    def _join_driver(self, timeout: Optional[float] = None):
        pass

    def compile(self,
                common_state: Optional[CommonState] = None,
                name: Optional[str] = None,
                handle_signals: bool = True):
        self.on_compile_begin()
        super().compile(common_state=common_state,
                        name=name,
                        handle_signals=handle_signals)
        self.on_compile_end()

    def start(self):
        self.logger.info("Starting node")
        if self.stopped():
            if self.joined():
                self._actions_before_start()
                self.on_start_begin()
                self._start_driver()
                self.on_start_end()
                self.logger.info("Node started")
            else:
                self.logger.error("Node stopped but not joined")
        else:
            self.logger.error("Node is already started")

    def stop(self):
        self.logger.info("Stopping node")
        if not self.stopped():
            self.on_stop_begin()
            self._stop_driver()
            self.on_stop_end()
            self._actions_after_stop()
            self.logger.info("Node stopped")
        else:
            self.logger.error("Node is already stopped")

    def join(self, timeout: Optional[float] = None):
        self.logger.info("Joining node")
        if not self.joined():
            self.on_join_begin()
            self._join_driver(timeout=timeout)
            self.on_join_end()
            self.logger.info("Node joined")
        else:
            self.logger.error("Node is already joined")

    def joined(self) -> bool:
        return self._driver is None
