from typing import Optional, Dict

from rosny.state import InternalState
from rosny.abstract import AbstractStream
from rosny.utils import setup_logger


class BaseComposeStream(AbstractStream):
    def __init__(self):
        super().__init__()
        self._streams: Dict[str, AbstractStream] = dict()

    def __setattr__(self, name, value):
        if isinstance(value, AbstractStream):
            self._streams[name] = value
        object.__setattr__(self, name, value)

    def compile(self,
                internal_state: Optional[InternalState] = None,
                name: Optional[str] = None):
        if not self._compiled:
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

            for stream_name, stream in self._streams.items():
                stream.compile(
                    internal_state=self._internal_state,
                    name=f"{self.name}/{stream_name}"
                )

            self._compiled = True

    def start(self):
        if not self._compiled:
            self.compile()
        self.logger.info(f"Start compose stream '{self.name}'")
        self.on_start_begin()
        for stream in self._streams.values():
            stream.start()
        self.on_start_end()
        self.logger.info(f"Compose stream '{self.name}' started")

    def wait(self, timeout: Optional[float] = None):
        self.logger.info(f"Stream start waiting with timeout {timeout}")
        self.on_wait_begin()
        self._internal_state.wait_exit(timeout=timeout)
        self.on_wait_end()
        if self._internal_state.exit_is_set():
            self.logger.info("Stream stop waiting, exit event is set")
        else:
            self.logger.info("Stream stop waiting, timeout exceeded")

    def stop(self):
        self.on_stop_begin()
        for stream in self._streams.values():
            stream.stop()
        self.on_stop_end()
        self.logger.info(f"Stop compose stream '{self.name}'")

    def join(self, timeout: Optional[float] = None):
        self.on_join_begin()
        for stream in self._streams.values():
            stream.join(timeout=timeout)
        self.on_join_end()
        self.logger.info(f"Compose stream '{self.name}' joined")
