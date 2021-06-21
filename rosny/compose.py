import abc
import time
from typing import Optional, Dict

from rosny.abstract import BaseStream, AbstractStream
from rosny.state import InternalState
from rosny.signal import start_signals, stop_signals


class ComposeStream(BaseStream, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self._streams: Dict[str, AbstractStream] = dict()

    def __setattr__(self, name, value):
        if isinstance(value, AbstractStream):
            self._streams[name] = value
        object.__setattr__(self, name, value)

    def compile(self,
                internal_state: Optional[InternalState] = None,
                name: Optional[str] = None,
                handle_signals: bool = True):
        super().compile(internal_state=internal_state, name=name)
        for stream_name, stream in self._streams.items():
            stream.compile(
                internal_state=self._internal_state,
                name=f"{self.name}/{stream_name}"
            )

    def start(self):
        if not self.compiled():
            self.compile()
        self.logger.info("Starting stream")
        self.on_start_begin()
        for stream in self._streams.values():
            stream.start()
        if self._handle_signals:
            start_signals(self)
        self.on_start_end()
        self.logger.info("Stream started")

    def stop(self):
        self.logger.info("Stopping stream")
        self.on_stop_begin()
        for stream in self._streams.values():
            stream.stop()
        if self._handle_signals:
            stop_signals(self)
        self.on_stop_end()
        self.logger.info("Stream stopped")

    def join(self, timeout: Optional[float] = None):
        self.logger.info("Joining stream")
        self.on_join_begin()
        for stream in self._streams.values():
            start = time.perf_counter()
            stream.join(timeout=timeout)
            if timeout is not None:
                timeout -= time.perf_counter() - start
                timeout = max(timeout, 0)
        self.on_join_end()
        self.logger.info("Stream joined")

    def stopped(self) -> bool:
        for stream in self._streams.values():
            if not stream.stopped():
                return False
        return True

    def joined(self) -> bool:
        for stream in self._streams.values():
            if not stream.joined():
                return False
        return True
