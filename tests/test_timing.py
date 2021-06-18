import time
import pytest


@pytest.mark.parametrize("start", [True, False])
def test_loop_time_meter(loop_time_meter, start):
    if start:
        time.sleep(0.1)
    for _ in range(100):
        if start:
            loop_time_meter.start()
        time.sleep(0.01)
        loop_time_meter.end()
    assert pytest.approx(loop_time_meter.mean, rel=6e-2) == 0.01
    loop_time_meter.reset()
    assert loop_time_meter.count == 0
