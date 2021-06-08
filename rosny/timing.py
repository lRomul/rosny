import time
from typing import Optional


class LoopTimeMeter:
    def __init__(self):
        self.mean = 0.0
        self.count = 0
        self.restart_time = time.perf_counter()
        self.prev_time = self.restart_time

    def start(self):
        self.prev_time = time.perf_counter()

    def end(self):
        self.count += 1
        now_time = time.perf_counter()
        delta = now_time - self.prev_time
        self.mean += (delta - self.mean) / self.count
        self.prev_time = now_time

    def reset(self):
        self.mean = 0.0
        self.count = 0
        self.restart_time = time.perf_counter()


class LoopRateManager:
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-7):
        self._time_meter = LoopTimeMeter()
        self._loop_sec = None
        self._mean_delta_sleep = None
        self._limit_loop_rate = None
        self._prev_work_time = time.perf_counter()
        self.loop_rate = loop_rate
        self.min_sleep = min_sleep

        self.loop_rate = loop_rate

    @property
    def loop_rate(self):
        return self._loop_rate

    @loop_rate.setter
    def loop_rate(self, value):
        self._loop_rate = value
        if value is None:
            self._loop_time = None
            self._mean_delta_sleep = None
        else:
            self._loop_time = 1.0 / self.loop_rate
            self._mean_delta_sleep = 0.

    def call(self):
        pass
