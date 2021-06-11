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
                 min_sleep: float = 1e-7,
                 profiler_interval: float = 1.0):
        self._time_meter = LoopTimeMeter()
        self._loop_time = None
        self._mean_delta_sleep = None
        self._loop_rate = None
        self._prev_work_time = time.perf_counter()

        self.loop_rate = loop_rate
        self.min_sleep = min_sleep
        self.profiler_interval = profiler_interval

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

    def _measure(self):
        loop_time = self._time_meter.mean
        # loop_rate = 1 / loop_time if loop_time else float('inf')

        if self._loop_rate is not None:
            self._mean_delta_sleep += loop_time - self._loop_time
            self._mean_delta_sleep = max(self._mean_delta_sleep, 0)

        self._time_meter.reset()

    def _sleep(self):
        if self._loop_rate is None:
            sleep_time = self.min_sleep
        else:
            sleep_time = (self._loop_time
                          + self._prev_work_time
                          - time.perf_counter())
            sleep_time -= self._mean_delta_sleep
            sleep_time = max(self.min_sleep, sleep_time)

        if sleep_time > 0:
            time.sleep(sleep_time)

    def timing(self):
        self._time_meter.end()
        if self._time_meter.prev_time - self._time_meter.restart_time \
                > self.profiler_interval:
            self._measure()
        self._sleep()
        self._prev_work_time = time.perf_counter()
