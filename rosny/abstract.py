import abc
import signal
from typing import Optional, Union

from rosny.state import InternalState
from rosny.timing import LoopRateManager
from rosny.utils import setup_logger, default_object_name


class AbstractStream(abc.ABC):
    @abc.abstractmethod
    def compile(self,
                internal_state: Optional[InternalState] = None,
                name: Optional[str] = None):
        pass

    def on_start_begin(self):
        pass

    def on_start_end(self):
        pass

    @abc.abstractmethod
    def start(self):
        pass

    def on_wait_begin(self):
        pass

    def on_wait_end(self):
        pass

    @abc.abstractmethod
    def wait(self, timeout: Optional[float] = None):
        pass

    def on_stop_begin(self):
        pass

    def on_stop_end(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    def on_join_begin(self):
        pass

    def on_join_end(self):
        pass

    @abc.abstractmethod
    def join(self, timeout: Optional[float] = None):
        pass

    @abc.abstractmethod
    def stopped(self) -> bool:
        pass

    @abc.abstractmethod
    def compiled(self) -> bool:
        pass

    @abc.abstractmethod
    def joined(self) -> bool:
        pass

    def __del__(self):
        if not self.stopped():
            self.stop()


class BaseStream(AbstractStream, abc.ABC):
    def __init__(self):
        self.name = default_object_name(self)
        self.logger = setup_logger(self.name)
        self._internal_state = InternalState()
        self._compiled = False

    def compile(self,
                internal_state: Optional[InternalState] = None,
                name: Optional[str] = None):
        self.name = self.__class__.__name__ if name is None else name
        self.logger = setup_logger(self.name)
        self._internal_state = (InternalState() if internal_state is None
                                else internal_state)
        self._init_signals()
        self._compiled = True

    def wait(self, timeout: Optional[float] = None):
        self.logger.info(f"Waiting stream with timeout {timeout}")
        self.on_wait_begin()
        self._internal_state.wait_exit(timeout=timeout)
        self.on_wait_end()
        if self._internal_state.exit_is_set():
            self.logger.info("Waiting ended, exit event is set")
        else:
            self.logger.info("Waiting ended, timeout exceeded")

    def _init_signals(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Handle signal: {signal.Signals(signum).name}")
        self._internal_state.set_exit()
        self.stop()

    def compiled(self) -> bool:
        return self._compiled


class LoopStream(BaseStream, abc.ABC):
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9):
        super().__init__()
        self._driver = None
        self.rate_manager = LoopRateManager(loop_rate=loop_rate,
                                            min_sleep=min_sleep)

    def work(self):
        pass

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

    @abc.abstractmethod
    def _start_driver(self):
        pass

    @abc.abstractmethod
    def _stop_driver(self):
        pass

    @abc.abstractmethod
    def _join_driver(self, timeout):
        pass

    def start(self):
        self.logger.info("Starting stream")
        if self.stopped():
            if self.joined():
                if not self.compiled():
                    self.compile()
                self.on_start_begin()
                self._start_driver()
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
