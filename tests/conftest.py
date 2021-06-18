import pytest

from rosny.timing import LoopTimeMeter


@pytest.fixture(scope='function')
def time_meter() -> LoopTimeMeter:
    return LoopTimeMeter()
