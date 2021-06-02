from threading import Thread
from typing import Optional

from rosny.basestate import BaseState
from rosny.abstract import AbstractStream


class BaseThreadStream(AbstractStream):
    def __init__(self,
                 state: Optional[BaseState] = None,
                 name: Optional[str] = None):
        super().__init__(state=state, name=name)

        self._thread = None
        self._stopped = True

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
        self.state.set_exit()

    def _start_thread(self):
        self._thread = Thread(target=self.work_loop,
                              name=self.name,
                              daemon=True)
        self._stopped = False
        self._thread.start()

    def _join_thread(self, timeout):
        self._thread.join(timeout)
        if self._thread.is_alive():
            self.logger.error(
                f"Thread '{self._thread}' join timeout {timeout}"
            )
        else:
            self._thread = None
            self.state.clear_exit()

    def start(self):
        self.logger.info("Starting stream")
        if self._stopped:
            if self._thread is None:
                self.on_start_begin()
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
