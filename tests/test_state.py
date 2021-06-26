import pytest
from rosny.state import CommonState


@pytest.fixture(scope='function')
def internal_state() -> CommonState:
    return CommonState()


class TestInternalState:
    def test_set_clear_exit_event(self, internal_state):
        assert not internal_state._exit_event.is_set()
        assert not internal_state.exit_is_set()
        internal_state.set_exit()
        assert internal_state._exit_event.is_set()
        assert internal_state.exit_is_set()
        internal_state.clear_exit()
        assert not internal_state._exit_event.is_set()
        assert not internal_state.exit_is_set()

    def test_state_wait_exit(self, internal_state, time_meter):
        assert not internal_state.exit_is_set()

        time_meter.start()
        internal_state.wait_exit(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, rel=0.05) == 0.1

        internal_state.set_exit()
        internal_state.wait_exit()
