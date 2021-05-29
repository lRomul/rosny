import signal
from threading import Thread
from typing import Optional

from rosny.state import State
from rosny.abstract import AbstractStream
from rosny.utils import setup_logger


class ThreadStream(AbstractStream):
    def __init__(self, state=None, name=None):
        if name is None:
            name = f"{self.__class__.__name__}_{id(self)}"
        self.logger = setup_logger(name)
        self.logger.info("Creating stream")

        self.name: str = name
        self.state = state

        self._thread = None
        self._stopped = True

        self._init_signals()

    def work(self):
        raise NotImplementedError

    def work_loop(self):
        try:
            while not self._stopped:
                self.work()
        except BaseException as exception:
            self.on_catch_exception(exception)

    def on_catch_exception(self, exception: BaseException):
        self.logger.exception(exception)
        if isinstance(self.state, State):
            self.state.set_exit()

    def _start_thread(self):
        self._thread = Thread(target=self.work_loop,
                              name=self.name,
                              daemon=True)
        self._thread.start()

    def _join_thread(self, timeout):
        self._thread.join(timeout)
        if self._thread.is_alive():
            self.logger.error(
                f"Thread '{self._thread}' join timeout {timeout}"
            )
        else:
            self._thread = None
            if isinstance(self.state, State):
                self.state.clear_exit()

    def start(self):
        self.logger.info("Starting stream")
        if self._stopped:
            if self._thread is None:
                self.on_start_begin()
                self._stopped = False
                self._start_thread()
                self.on_start_end()
                self.logger.info("Stream started")
            else:
                self.logger.error("Stream stopped but not joined")
        else:
            self.logger.error("Stream is already started")

    def stop(self):
        if not self._stopped:
            self.on_stop_begin()
            self._stopped = True
            self.on_stop_end()
            self.logger.info("Stop stream")

    def wait(self, timeout: Optional[float] = None):
        self.logger.info(
            f"Stream start waiting with timeout {timeout}"
        )
        self.on_wait_begin()
        self.state.wait_exit(timeout=timeout)
        self.on_wait_end()
        if self.state.exit_is_set():
            self.logger.info(
                "Stream stop waiting, exit event is set"
            )
        else:
            self.logger.info(
                "Stream stop waiting, timeout exceeded."
            )

    def join(self, timeout: Optional[float] = None):
        if self._thread is not None:
            self.on_join_begin()
            self._join_thread(timeout=timeout)
            self.on_join_end()
            self.logger.info("Stream joined")
        else:
            self.logger.error("Stream is already joined")

    def _init_signals(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Handle signal: {signal.Signals(signum).name}")
        if isinstance(self.state, State):
            self.state.set_exit()
        self.stop()

    def __del__(self):
        self.stop()
