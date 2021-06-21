import os
import time
import signal
import pytest
from typing import Optional
from multiprocessing import Process, Value

from rosny.process import ProcessStream
from rosny.signal import SignalException


class CustomStream(ProcessStream):
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


@pytest.fixture(scope='function')
def stream():
    stream = CustomStream()
    yield stream
    stream.stop()
    stream.join()


class TestProcessStream:
    def test_init(self):
        stream = CustomStream(loop_rate=30.0, min_sleep=0.001)
        assert stream.init_param is None
        assert stream.another_param == 43
        stream.compile()
        assert stream.rate_manager.loop_rate == 30.0
        assert stream.rate_manager.min_sleep == 0.001

        stream = CustomStream(init_param=42)
        assert stream.init_param == 42
        assert stream.another_param == 43
        assert stream.rate_manager.loop_rate is None
        assert stream.rate_manager.min_sleep == 1e-9

    def test_compile(self, stream: CustomStream):
        assert not stream.compiled()
        assert not stream._compiled
        assert stream.name.startswith('CustomStream-')
        assert stream.name == stream.logger.name
        stream.compile()
        assert stream.compiled()
        assert stream._compiled
        assert stream.name == 'CustomStream'
        assert stream.logger.name == 'CustomStream'

    def test_start(self, stream: CustomStream):
        assert not stream.compiled()
        assert stream.stopped()
        assert stream.joined()
        stream.start()
        assert stream.compiled()
        assert not stream.stopped()
        assert not stream.joined()
        assert isinstance(stream._driver, Process)
        assert stream._driver.is_alive()

    def test_wait(self, stream: CustomStream, time_meter):
        time_meter.start()
        stream.start()
        stream.wait(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, abs=0.05) == 0.1

    def test_stop(self, stream: CustomStream):
        stream.start()
        stream.wait(timeout=0.01)
        assert not stream.stopped()
        stream.stop()
        assert stream.stopped()

    def test_join(self, stream: CustomStream):
        stream.start()
        stream.wait(timeout=0.01)
        stream.stop()
        assert stream.stopped()
        assert not stream.joined()
        assert isinstance(stream._driver, Process)
        stream.join()
        assert stream.stopped()
        assert stream.joined()
        assert stream._driver is None

    def test_loop_rate_work(self, stream: CustomStream):
        stream.rate_manager.loop_rate = 120
        stream.start()
        stream.wait(timeout=3.0)
        assert pytest.approx(stream.count.value, rel=0.1) == 360

    def test_join_timeout(self, time_meter):
        class SleepStream(ProcessStream):
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

    def test_min_sleep(self, stream: CustomStream):
        stream.rate_manager.min_sleep = 0.01
        stream.start()
        stream.wait(timeout=0.1)
        assert stream.count.value <= 11

    def test_double_start(self, stream: CustomStream):
        assert stream._driver is None
        stream.start()
        assert isinstance(stream._driver, Process)
        process = stream._driver
        stream.start()
        assert stream._driver is process
        stream.stop()
        stream.join()
        assert stream._driver is None

    def test_restart(self, stream: CustomStream):
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

    def test_wrong_restart(self, stream: CustomStream):
        stream.start()
        process = stream._driver
        stream.wait(timeout=1)
        assert not stream.stopped()
        stream.stop()
        assert stream._driver is process
        assert stream.stopped()

        stream.start()
        assert stream._driver is process
        assert stream.stopped()

        stream.join()
        assert stream._driver is None
        assert stream.joined()

    def test_exception_catching(self):
        class ExceptionStream(ProcessStream):
            def __init__(self):
                super().__init__()
                self.exception = Value('i', 0)

            def work(self):
                time.sleep(0.1)
                raise Exception("test")

            def on_catch_exception(self, exception):
                self.exception.value = 1
                super().on_catch_exception(exception)

        stream = ExceptionStream()
        stream.start()
        stream.wait()
        assert stream.exception.value
        stream.stop()
        stream.join()

    def test_handle_signal(self, stream: CustomStream):
        stream.start()
        time.sleep(0.1)
        with pytest.raises(SignalException):
            os.kill(os.getpid(), signal.SIGINT)
            stream.wait()
        stream.stop()
        assert stream.stopped()
        stream.join()
        assert stream.joined()
