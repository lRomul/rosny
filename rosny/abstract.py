import abc
import signal
import logging
from typing import Optional

from rosny.basestate import BaseState
from rosny.utils import setup_logger, default_object_name


class AbstractStream(abc.ABC):
    name: str
    state: BaseState
    logger: logging.Logger

    def __init__(self,
                 state: Optional[BaseState] = None,
                 name: Optional[str] = None):
        self._name: str = ""
        self.name = name
        self.state = state
        self._init_signals()
        self.logger.info("Creating stream")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: Optional[str]):
        if name is None:
            name = default_object_name(self)
        self.logger = setup_logger(name)
        self._name: str = name

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

    def _init_signals(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Handle signal: {signal.Signals(signum).name}")
        self.state.set_exit()
        self.stop()

    def __del__(self):
        self.stop()
