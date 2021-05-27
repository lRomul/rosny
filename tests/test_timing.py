import time
import pytest

from rosny.timing import LoopTimeMeter


@pytest.mark.parametrize("start", [True, False])
def test_delta_time_profiler(start):
    profiler = LoopTimeMeter()

    if start:
        time.sleep(0.1)
    for _ in range(100):
        if start:
            profiler.start()
        time.sleep(0.01)
        profiler.end()
    assert pytest.approx(profiler.mean, rel=6e-2) == 0.01
    profiler.reset()
    assert profiler.count == 0
