import abc
from typing import Optional

from rosny.state import CommonState
from rosny.utils import setup_logger, default_object_name


class AbstractStream(metaclass=abc.ABCMeta):
    def on_compile_begin(self):
        pass

    def on_compile_end(self):
        pass

    @abc.abstractmethod
    def compile(self,
                common_state: Optional[CommonState] = None,
                name: Optional[str] = None):
        pass

    def on_start_begin(self):
        pass

    def on_start_end(self):
        pass

    @abc.abstractmethod
    def start(self):
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


class BaseStream(AbstractStream, metaclass=abc.ABCMeta):
    def __init__(self):
        self.name = default_object_name(self)
        self.logger = setup_logger(self.name)
        self.common_state = CommonState()
        self._compiled = False
        self._handle_signals = False

    def compile(self,
                common_state: Optional[CommonState] = None,
                name: Optional[str] = None):
        self.name = self.__class__.__name__ if name is None else name
        self.logger = setup_logger(self.name)
        if common_state is None:  # is it root stream
            self._handle_signals = True
        else:
            self.common_state = common_state
        self._compiled = True

    def wait(self, timeout: Optional[float] = None):
        self.logger.info(f"Waiting stream with timeout {timeout}")
        self.common_state.wait_exit(timeout=timeout)
        if self.common_state.exit_is_set():
            self.logger.info("Waiting ended, exit event is set")
        else:
            self.logger.info("Waiting ended, timeout exceeded")

    def compiled(self) -> bool:
        return self._compiled

    def __del__(self):
        if not self.stopped():
            self.stop()
