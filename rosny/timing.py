import time
from typing import Optional

from rosny.abstract import BaseStream


class LoopTimeMeter:
    def __init__(self):
        self.mean = 0.0
        self.count = 0
        self.last_time = time.perf_counter()

    def reset(self):
        self.mean = 0.0
        self.count = 0
        self.last_time = time.perf_counter()

    def start(self):
        self.last_time = time.perf_counter()

    def end(self):
        self.count += 1
        now_time = time.perf_counter()
        delta = now_time - self.last_time
        self.mean += (delta - self.mean) / self.count
        self.last_time = now_time


class LoopRateManager:
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9):
        self._loop_rate = None
        self._loop_time = None
        self._sleep_delay = None
        self._prev_delay_time = time.perf_counter()
        self._prev_sleep_time = time.perf_counter()

        self.loop_rate = loop_rate
        self.min_sleep = min_sleep

    def _build(self, loop_rate):
        self._loop_rate = loop_rate
        if loop_rate is None:
            self._loop_time = None
            self._sleep_delay = None
        else:
            self._loop_time = 1.0 / self.loop_rate
            self._sleep_delay = 0.
        self._prev_delay_time = time.perf_counter()
        self._prev_sleep_time = time.perf_counter()

    def reset(self):
        self._build(self._loop_rate)

    @property
    def loop_rate(self):
        return self._loop_rate

    @loop_rate.setter
    def loop_rate(self, value):
        self._build(value)

    def timing(self):
        if self._loop_rate is None:
            if self.min_sleep:
                time.sleep(self.min_sleep)
        else:
            now_time = time.perf_counter()
            self._sleep_delay += (now_time
                                  - self._prev_delay_time
                                  - self._loop_time) * self._loop_time
            self._sleep_delay = max(self._sleep_delay, 0)
            self._prev_delay_time = now_time

            sleep_time = (self._loop_time
                          + self._prev_sleep_time
                          - time.perf_counter()
                          - self._sleep_delay)
            sleep_time = max(self.min_sleep, sleep_time)
            time.sleep(sleep_time)
            self._prev_sleep_time = time.perf_counter()


class Profiler:
    def __init__(self, stream: BaseStream, interval: Optional[float] = None):
        self._stream = stream
        self.interval = interval
        self._time_meter = LoopTimeMeter()
        self._last_profile_time = time.perf_counter()

    def reset(self, stream: BaseStream):
        self._stream = stream
        self._time_meter.reset()
        self._last_profile_time = time.perf_counter()

    def profile(self):
        if self.interval is not None:
            self._time_meter.end()
            if self._time_meter.last_time - self._last_profile_time > self.interval:
                loop_time = self._time_meter.mean
                loop_rate = 1 / loop_time if loop_time else float('inf')
                self._stream.common_state.profile_stats[self._stream.name] = loop_time
                self._stream.logger.info(
                    f"Profile - loop time {loop_time:.6g}, loop rate {loop_rate:.4g}"
                )

                self._time_meter.reset()
                self._last_profile_time = time.perf_counter()
