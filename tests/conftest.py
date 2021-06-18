import pytest

from rosny.timing import LoopTimeMeter


@pytest.fixture(scope='function')
def loop_time_meter() -> LoopTimeMeter:
    return LoopTimeMeter()
