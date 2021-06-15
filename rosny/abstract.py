import abc
import signal
from typing import Optional

from rosny.state import InternalState
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

    def __del__(self):
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
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name
        self.logger = setup_logger(self.name)

        if internal_state is None:
            self._internal_state = InternalState()
        else:
            self._internal_state = internal_state

        self._init_signals()
        self._compiled = True

    def _init_signals(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Handle signal: {signal.Signals(signum).name}")
        self._internal_state.set_exit()
        self.stop()
