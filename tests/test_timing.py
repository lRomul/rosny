import time
import pytest

from rosny.timing import LoopTimeMeter


@pytest.mark.parametrize("start", [True, False])
def test_loop_time_meter(start):
    meter = LoopTimeMeter()

    if start:
        time.sleep(0.1)
    for _ in range(100):
        if start:
            meter.start()
        time.sleep(0.01)
        meter.end()
    assert pytest.approx(meter.mean, rel=6e-2) == 0.01
    meter.reset()
    assert meter.count == 0
