import abc
import time
from typing import Optional, Dict

from rosny.abstract import BaseNode, AbstractNode
from rosny.state import CommonState


class ComposeNode(BaseNode, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self._nodes: Dict[str, AbstractNode] = dict()

    def __setattr__(self, name, value):
        if isinstance(value, AbstractNode):
            self._nodes[name] = value
        object.__setattr__(self, name, value)

    def compile(self,
                common_state: Optional[CommonState] = None,
                name: Optional[str] = None,
                handle_signals: bool = True):
        self.on_compile_begin()
        super().compile(common_state=common_state,
                        name=name,
                        handle_signals=handle_signals)
        for node_name, node in self._nodes.items():
            node.compile(
                common_state=self.common_state,
                name=f"{self.name}/{node_name}",
                handle_signals=False
            )
        self.on_compile_end()

    def start(self):
        self.logger.info("Starting node")
        self._actions_before_start()
        self.on_start_begin()
        for node in self._nodes.values():
            node.start()
        self.on_start_end()
        self.logger.info("Node started")

    def stop(self):
        self.logger.info("Stopping node")
        self.on_stop_begin()
        for node in self._nodes.values():
            node.stop()
        self.on_stop_end()
        self._actions_after_stop()
        self.logger.info("Node stopped")

    def join(self, timeout: Optional[float] = None):
        self.logger.info("Joining node")
        self.on_join_begin()
        for node in self._nodes.values():
            start = time.perf_counter()
            node.join(timeout=timeout)
            if timeout is not None:
                timeout -= time.perf_counter() - start
                timeout = max(timeout, 0)
        self.on_join_end()
        self.logger.info("Node joined")

    def stopped(self) -> bool:
        for node in self._nodes.values():
            if not node.stopped():
                return False
        return True

    def joined(self) -> bool:
        for node in self._nodes.values():
            if not node.joined():
                return False
        return True
