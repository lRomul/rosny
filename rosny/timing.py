import time
from typing import Optional

from rosny.utils import EMAMeter


class LoopRateManager:
    def __init__(self,
                 loop_rate: Optional[float] = None,
                 min_sleep: float = 1e-9):
        self._loop_rate = None
        self._loop_time = None
        self._sleep_delay_meter = None
        self._prev_time = time.perf_counter()
        self._prev_loop_time = self._loop_time

        self.min_sleep = min_sleep
        self._build(loop_rate)

    def _build(self, loop_rate):
        self._loop_rate = loop_rate
        if loop_rate is None:
            self._loop_time = None
            self._sleep_delay_meter = None
        else:
            self._loop_time = 1.0 / self.loop_rate
            self._sleep_delay_meter = EMAMeter(
                alpha=2 / (self.loop_rate + 1)
            )
        self._prev_loop_time = self._loop_time
        self._prev_time = time.perf_counter()

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
            sleep_time = self.min_sleep
        else:
            now = time.perf_counter()
            self._sleep_delay_meter.update(self._prev_loop_time - self._loop_time)
            sleep_time = self._loop_time - (now - self._prev_time)
            sleep_time -= self._sleep_delay_meter.mean
            sleep_time = max(self.min_sleep, sleep_time)

        time.sleep(sleep_time)
        now = time.perf_counter()
        self._prev_loop_time = now - self._prev_time
        self._prev_time = now
