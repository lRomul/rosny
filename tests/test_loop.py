import os
import time
import signal
import pytest
from typing import Optional
from multiprocessing import Value, Manager

from rosny import CommonState, ThreadNode, ProcessNode
from rosny.signal import SignalException


@pytest.fixture(scope='module', params=[ThreadNode, ProcessNode])
def loop_node_class(request):
    return request.param


@pytest.fixture(scope='module')
def custom_node_class(loop_node_class):
    class CustomNode(loop_node_class):
        def __init__(self,
                     loop_rate: Optional[float] = None,
                     min_sleep: float = 1e-9,
                     init_param=None,
                     another_param=43):
            super().__init__(loop_rate=loop_rate, min_sleep=min_sleep)
            self.init_param = init_param
            self.another_param = another_param
            self.count = Value('i', 0)

        def work(self):
            self.count.value += 1

    return CustomNode


@pytest.fixture(scope='function')
def node(custom_node_class):
    node = custom_node_class()
    yield node
    node.stop()
    node.join()


class TestLoopNode:
    def test_init(self, custom_node_class):
        node = custom_node_class(loop_rate=30.0, min_sleep=0.001)
        assert node.init_param is None
        assert node.another_param == 43
        node.compile()
        assert node.rate_manager.loop_rate == 30.0
        assert node.rate_manager.min_sleep == 0.001

        node = custom_node_class(init_param=42)
        assert node.init_param == 42
        assert node.another_param == 43
        assert node.rate_manager.loop_rate is None
        assert node.rate_manager.min_sleep == 1e-9

    def test_compile(self, node):
        assert not node.compiled()
        assert not node._compiled
        assert node.name.startswith('CustomNode-')
        assert node.name == node.logger.name
        node.compile()
        assert node.compiled()
        assert node._compiled
        assert node.name == 'CustomNode'
        assert node.logger.name == 'CustomNode'

    def test_compile_arguments(self, node):
        state = CommonState()
        assert not node.compiled()
        assert not node._compiled
        assert node.name.startswith('CustomNode-')
        assert node.name == node.logger.name
        node.compile(common_state=state, name='node_name', handle_signals=False)
        assert node.compiled()
        assert node._compiled
        assert node.name == 'node_name'
        assert node.logger.name == 'node_name'
        assert node.common_state is state
        assert not node.handle_signals

    def test_start(self, node):
        assert not node.compiled()
        assert node.stopped()
        assert node.joined()
        node.start()
        assert node.compiled()
        assert not node.stopped()
        assert not node.joined()
        assert node._driver.is_alive()

    def test_wait(self, node, time_meter):
        time_meter.start()
        node.start()
        node.wait(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, abs=0.05) == 0.1

    def test_stop(self, node):
        node.start()
        node.wait(timeout=0.01)
        assert not node.stopped()
        node.stop()
        assert node.stopped()

    def test_join(self, node):
        node.start()
        node.wait(timeout=0.01)
        node.stop()
        assert node.stopped()
        assert not node.joined()
        node.join()
        assert node.stopped()
        assert node.joined()
        assert node._driver is None

    def test_loop_rate_work(self, node):
        node.rate_manager.loop_rate = 60
        node.profiler.interval = 1
        node.start()
        node.wait(timeout=3.0)
        assert pytest.approx(node.count.value, rel=0.05) == 180
        loop_time = node.common_state.profile_stats[node.name]
        assert pytest.approx(loop_time, rel=0.05) == 1 / 60

    def test_join_timeout(self, loop_node_class, time_meter):
        class SleepNode(loop_node_class):
            def work(self):
                time.sleep(3)

        node = SleepNode()
        node.start()
        node.wait(1)
        node.stop()
        assert not node.joined()
        time_meter.start()
        node.join(timeout=1)
        time_meter.end()
        assert not node.joined()
        assert pytest.approx(time_meter.mean, rel=0.05) == 1
        node.join()
        assert node.joined()

    def test_min_sleep(self, node):
        node.rate_manager.min_sleep = 0.1
        node.start()
        node.wait(timeout=1)
        assert node.count.value <= 11

    def test_double_start(self, node):
        assert node._driver is None
        node.start()
        driver = node._driver
        node.start()
        assert node._driver is driver
        node.wait(0.1)
        node.stop()
        node.join()
        assert node._driver is None

        assert node.compiled() and node.stopped() and node.joined()
        node.start()
        assert node.compiled() and not node.stopped() and not node.joined()
        new_driver = node._driver
        assert new_driver is not driver
        node.wait(0.1)
        node.stop()
        assert node._driver is new_driver
        node.join()
        assert node._driver is None

    def test_restart(self, node):
        node.start()
        node.wait(timeout=1)
        assert not node.stopped()
        node.stop()
        node.join()
        assert node.joined()
        assert node.stopped()

        node.start()
        node.wait(timeout=1)
        assert not node.stopped()
        node.stop()
        node.join()
        assert node.joined()
        assert node.stopped()
        assert node.count.value > 30

    def test_wrong_restart(self, node):
        node.start()
        driver = node._driver
        node.wait(timeout=1)
        assert not node.stopped()
        node.stop()
        assert node._driver is driver
        assert node.stopped()

        node.start()
        assert node._driver is driver
        assert node.stopped()

        node.join()
        assert node._driver is None
        assert node.joined()

    def test_callbacks(self, loop_node_class):
        class CallbackNode(loop_node_class):
            def __init__(self):
                super().__init__()
                self.manager = Manager()
                self.callback_history = self.manager.list([])

            def work(self):
                time.sleep(0.1)
                raise Exception("test")

            def on_catch_exception(self, exception):
                self.callback_history += ['on_catch_exception']
                super().on_catch_exception(exception)

            def on_loop_begin(self):
                self.callback_history += ['on_loop_begin']

            def on_loop_end(self):
                self.callback_history += ['on_loop_end']

        node = CallbackNode()
        node.start()
        node.wait()
        time.sleep(0.1)
        assert node.callback_history[:] == [
            'on_loop_begin', 'on_catch_exception', 'on_loop_end'
        ]
        node.stop()
        node.join()

    def test_handle_signal(self, node):
        node.start()
        time.sleep(0.1)
        with pytest.raises(SignalException):
            os.kill(os.getpid(), signal.SIGINT)
            node.wait()
        node.stop()
        assert node.stopped()
        node.join()
        assert node.joined()

    @pytest.mark.parametrize("daemon", [True, False])
    def test_daemon(self, loop_node_class, daemon):
        class DaemonNode(loop_node_class):
            def __init__(self, daemon):
                super().__init__(daemon=daemon)

            def work(self):
                time.sleep(0.1)

        node = DaemonNode(daemon)
        node.start()
        assert node._driver.daemon == daemon
        node.stop()
        node.join()

    def test_del_not_stopped(self, custom_node_class):
        node = custom_node_class()
        node.start()
        node.__del__()
