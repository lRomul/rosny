import abc
import time
from typing import Optional, Dict

from rosny.abstract import BaseStream, AbstractStream
from rosny.state import CommonState


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
                common_state: Optional[CommonState] = None,
                name: Optional[str] = None,
                handle_signals: bool = True):
        self.on_compile_begin()
        super().compile(common_state=common_state,
                        name=name,
                        handle_signals=handle_signals)
        for stream_name, stream in self._streams.items():
            stream.compile(
                common_state=self.common_state,
                name=f"{self.name}/{stream_name}",
                handle_signals=False
            )
        self.on_compile_end()

    def start(self):
        self.logger.info("Starting stream")
        self._actions_before_start()
        self.on_start_begin()
        for stream in self._streams.values():
            stream.start()
        self.on_start_end()
        self.logger.info("Stream started")

    def stop(self):
        self.logger.info("Stopping stream")
        self.on_stop_begin()
        for stream in self._streams.values():
            stream.stop()
        self.on_stop_end()
        self._actions_after_stop()
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
