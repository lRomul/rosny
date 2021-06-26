import pytest
from rosny.state import CommonState


@pytest.fixture(scope='function')
def common_state() -> CommonState:
    return CommonState()


class TestCommonState:
    def test_set_clear_exit_event(self, common_state):
        assert not common_state._exit_event.is_set()
        assert not common_state.exit_is_set()
        common_state.set_exit()
        assert common_state._exit_event.is_set()
        assert common_state.exit_is_set()
        common_state.clear_exit()
        assert not common_state._exit_event.is_set()
        assert not common_state.exit_is_set()

    def test_state_wait_exit(self, common_state, time_meter):
        assert not common_state.exit_is_set()

        time_meter.start()
        common_state.wait_exit(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, rel=0.05) == 0.1

        common_state.set_exit()
        common_state.wait_exit()

    def test_get_set_state(self, common_state):
        state = common_state.__getstate__()
        common_state.__setstate__(state)
        assert common_state._manager is None
