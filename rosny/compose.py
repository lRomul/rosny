from typing import Optional, List

from rosny.state import BaseState
from rosny.abstract import AbstractStream


class BaseComposeStream(AbstractStream):
    def __init__(self,
                 state: Optional[BaseState] = None,
                 name: Optional[str] = None):
        super().__init__(state=state, name=name)

        self._streams: List[AbstractStream] = list()

    def __setattr__(self, name, value):
        if isinstance(value, AbstractStream):
            if value.state is None and self.state is not None:
                value.state = self.state
            self._streams.append(value)
        object.__setattr__(self, name, value)

    def start(self):
        self.logger.info(f"Start compose stream '{self.name}'")
        self.on_start_begin()
        for stream in self._streams:
            stream.start()
        self.on_start_end()
        self.logger.info(f"Compose stream '{self.name}' started")

    def wait(self, timeout: Optional[float] = None):
        self.logger.info(f"Stream start waiting with timeout {timeout}")
        self.on_wait_begin()
        self.state.wait_exit(timeout=timeout)
        self.on_wait_end()
        if self.state.exit_is_set():
            self.logger.info("Stream stop waiting, exit event is set")
        else:
            self.logger.info("Stream stop waiting, timeout exceeded")

    def stop(self):
        self.on_stop_begin()
        for stream in self._streams:
            stream.stop()
        self.on_stop_end()
        self.logger.info(f"Stop compose stream '{self.name}'")

    def join(self, timeout: Optional[float] = None):
        self.on_join_begin()
        for stream in self._streams:
            stream.join(timeout=timeout)
        self.on_join_end()
        self.logger.info(f"Compose stream '{self.name}' joined")
