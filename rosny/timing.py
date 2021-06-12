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
                 min_sleep: float = 1e-9):
        self._time_meter = LoopTimeMeter()
        self._loop_time = None
        self._sleep_delay = None
        self._loop_rate = None
        self._prev_time = time.perf_counter()

        self.loop_rate = loop_rate
        self.min_sleep = min_sleep

    @property
    def loop_rate(self):
        return self._loop_rate

    @loop_rate.setter
    def loop_rate(self, value):
        self._loop_rate = value
        if value is None:
            self._loop_time = None
            self._sleep_delay = None
        else:
            self._loop_time = 1.0 / self.loop_rate
            self._sleep_delay = 0.

    def timing(self):
        self._time_meter.end()

        if self._loop_rate is None:
            sleep_time = self.min_sleep
        else:
            self._sleep_delay += self._time_meter.mean - self._loop_time
            self._sleep_delay = max(self._sleep_delay, 0)

            sleep_time = (self._loop_time
                          + self._prev_time
                          - time.perf_counter())
            sleep_time -= self._sleep_delay
            sleep_time = max(self.min_sleep, sleep_time)

        time.sleep(sleep_time)
        self._prev_time = time.perf_counter()
