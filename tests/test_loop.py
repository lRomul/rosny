import os
import time
import signal
import pytest
from typing import Optional
from multiprocessing import Value, Manager

from rosny import CommonState, ThreadStream, ProcessStream
from rosny.signal import SignalException


@pytest.fixture(scope='module', params=[ThreadStream, ProcessStream])
def loop_stream_class(request):
    return request.param


@pytest.fixture(scope='module')
def custom_stream_class(loop_stream_class):
    class CustomStream(loop_stream_class):
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

    return CustomStream


@pytest.fixture(scope='function')
def stream(custom_stream_class):
    stream = custom_stream_class()
    yield stream
    stream.stop()
    stream.join()


class TestProcessStream:
    def test_init(self, custom_stream_class):
        stream = custom_stream_class(loop_rate=30.0, min_sleep=0.001)
        assert stream.init_param is None
        assert stream.another_param == 43
        stream.compile()
        assert stream.rate_manager.loop_rate == 30.0
        assert stream.rate_manager.min_sleep == 0.001

        stream = custom_stream_class(init_param=42)
        assert stream.init_param == 42
        assert stream.another_param == 43
        assert stream.rate_manager.loop_rate is None
        assert stream.rate_manager.min_sleep == 1e-9

    def test_compile(self, stream):
        assert not stream.compiled()
        assert not stream._compiled
        assert stream.name.startswith('CustomStream-')
        assert stream.name == stream.logger.name
        stream.compile()
        assert stream.compiled()
        assert stream._compiled
        assert stream.name == 'CustomStream'
        assert stream.logger.name == 'CustomStream'

    def test_compile_arguments(self, stream):
        state = CommonState()
        assert not stream.compiled()
        assert not stream._compiled
        assert stream.name.startswith('CustomStream-')
        assert stream.name == stream.logger.name
        stream.compile(common_state=state, name='stream_name', handle_signals=False)
        assert stream.compiled()
        assert stream._compiled
        assert stream.name == 'stream_name'
        assert stream.logger.name == 'stream_name'
        assert stream.common_state is state
        assert not stream.handle_signals

    def test_start(self, stream):
        assert not stream.compiled()
        assert stream.stopped()
        assert stream.joined()
        stream.start()
        assert stream.compiled()
        assert not stream.stopped()
        assert not stream.joined()
        assert stream._driver.is_alive()

    def test_wait(self, stream, time_meter):
        time_meter.start()
        stream.start()
        stream.wait(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, abs=0.05) == 0.1

    def test_stop(self, stream):
        stream.start()
        stream.wait(timeout=0.01)
        assert not stream.stopped()
        stream.stop()
        assert stream.stopped()

    def test_join(self, stream):
        stream.start()
        stream.wait(timeout=0.01)
        stream.stop()
        assert stream.stopped()
        assert not stream.joined()
        stream.join()
        assert stream.stopped()
        assert stream.joined()
        assert stream._driver is None

    def test_loop_rate_work(self, stream):
        stream.rate_manager.loop_rate = 120
        stream.profiler.interval = 1
        stream.start()
        stream.wait(timeout=3.0)
        assert pytest.approx(stream.count.value, rel=0.05) == 360
        loop_time = stream.common_state.profile_stats[stream.name]
        assert pytest.approx(loop_time, rel=0.05) == 1 / 120

    def test_join_timeout(self, loop_stream_class, time_meter):
        class SleepStream(loop_stream_class):
            def work(self):
                time.sleep(3)

        stream = SleepStream()
        stream.start()
        stream.wait(1)
        stream.stop()
        assert not stream.joined()
        time_meter.start()
        stream.join(timeout=1)
        time_meter.end()
        assert not stream.joined()
        assert pytest.approx(time_meter.mean, rel=0.05) == 1
        stream.join()
        assert stream.joined()

    def test_min_sleep(self, stream):
        stream.rate_manager.min_sleep = 0.1
        stream.start()
        stream.wait(timeout=1)
        assert stream.count.value <= 11

    def test_double_start(self, stream):
        assert stream._driver is None
        stream.start()
        driver = stream._driver
        stream.start()
        assert stream._driver is driver
        stream.stop()
        stream.join()
        assert stream._driver is None

    def test_restart(self, stream):
        stream.start()
        stream.wait(timeout=1)
        assert not stream.stopped()
        stream.stop()
        stream.join()
        assert stream.joined()
        assert stream.stopped()

        stream.start()
        stream.wait(timeout=1)
        assert not stream.stopped()
        stream.stop()
        stream.join()
        assert stream.joined()
        assert stream.stopped()
        assert stream.count.value > 30

    def test_wrong_restart(self, stream):
        stream.start()
        driver = stream._driver
        stream.wait(timeout=1)
        assert not stream.stopped()
        stream.stop()
        assert stream._driver is driver
        assert stream.stopped()

        stream.start()
        assert stream._driver is driver
        assert stream.stopped()

        stream.join()
        assert stream._driver is None
        assert stream.joined()

    def test_callbacks(self, loop_stream_class):
        class CallbackStream(loop_stream_class):
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

            def on_work_loop_begin(self):
                self.callback_history += ['on_work_loop_begin']

            def on_work_loop_end(self):
                self.callback_history += ['on_work_loop_end']

        stream = CallbackStream()
        stream.start()
        stream.wait()
        time.sleep(0.1)
        assert stream.callback_history[:] == [
            'on_work_loop_begin', 'on_catch_exception', 'on_work_loop_end'
        ]
        stream.stop()
        stream.join()

    def test_handle_signal(self, stream):
        stream.start()
        time.sleep(0.1)
        with pytest.raises(SignalException):
            os.kill(os.getpid(), signal.SIGINT)
            stream.wait()
        stream.stop()
        assert stream.stopped()
        stream.join()
        assert stream.joined()

    @pytest.mark.parametrize("daemon", [True, False])
    def test_daemon(self, loop_stream_class, daemon):
        class DaemonStream(loop_stream_class):
            def __init__(self, daemon):
                super().__init__(daemon=daemon)

            def work(self):
                time.sleep(0.1)

        stream = DaemonStream(daemon)
        stream.start()
        assert stream._driver.daemon == daemon
        stream.stop()
        stream.join()
