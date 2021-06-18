import time
import pytest

from rosny.timing import LoopRateManager


@pytest.mark.parametrize("start", [True, False])
def test_loop_time_meter(time_meter, start):
    time_meter.reset()
    if start:
        time.sleep(0.1)
    for _ in range(100):
        if start:
            time_meter.start()
        time.sleep(0.01)
        time_meter.end()
    assert pytest.approx(time_meter.mean, rel=0.05) == 0.01

    time_meter.reset()
    assert time_meter.mean == 0.0
    assert time_meter.count == 0
    time.sleep(0.1)
    time_meter.end()
    assert pytest.approx(time_meter.mean, rel=0.05) == 0.1


class TestLoopRateManager:
    @pytest.mark.parametrize("loop_rate", [12, 42, 120])
    def test_loop_rate_timing(self, loop_rate, time_meter):
        rate_manager = LoopRateManager(loop_rate=loop_rate)
        time_meter.reset()
        for _ in range(3 * loop_rate):
            rate_manager.timing()
            time_meter.end()
        assert pytest.approx(time_meter.mean, rel=0.05) == 1 / loop_rate

        # test of loop rate changing
        rate_manager.loop_rate = loop_rate * 2
        time_meter.reset()
        for _ in range(3 * loop_rate):
            rate_manager.timing()
            time_meter.end()
        assert pytest.approx(time_meter.mean, rel=0.05) == 1 / (loop_rate * 2)

        # test reset
        rate_manager.reset()
        assert rate_manager._sleep_delay == 0.
        assert rate_manager._time_meter.mean == 0.0
        assert rate_manager._loop_time == 1 / (loop_rate * 2)

    def test_no_limit_loop_timing(self, time_meter):
        rate_manager = LoopRateManager(loop_rate=None)
        time_meter.reset()
        for _ in range(1000):
            rate_manager.timing()
            time_meter.end()
        assert time_meter.mean < 0.001

    def test_min_sleep(self, time_meter):
        rate_manager = LoopRateManager(loop_rate=None, min_sleep=0.001)
        time_meter.reset()
        for _ in range(100):
            rate_manager.timing()
            time_meter.end()
        assert time_meter.mean > 0.001
