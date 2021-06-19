import time
import pytest

from rosny import ThreadStream, ComposeStream
from rosny.abstract import AbstractStream


class CountState:
    def __init__(self):
        self.count1 = 0
        self.count2 = 0


class CustomStream1(ThreadStream):
    def __init__(self, state):
        super().__init__(loop_rate=120)
        self.state = state

    def work(self):
        self.state.count1 += 1


class CustomStream2(ThreadStream):
    def __init__(self, state):
        super().__init__(loop_rate=60)
        self.state = state

    def work(self):
        self.state.count2 += 1


class CustomComposeStream(ComposeStream):
    def __init__(self):
        super().__init__()
        self.state = CountState()
        self.stream1 = CustomStream1(self.state)
        self.stream2 = CustomStream2(self.state)


@pytest.fixture(scope='function')
def compose_stream():
    stream = CustomComposeStream()
    yield stream
    stream.stop()
    stream.join()


class TestBaseComposeStream:
    def test_init(self):
        stream = CustomComposeStream()
        assert stream.name.startswith('CustomComposeStream-')
        assert isinstance(stream.state, CountState)
        assert len(stream._streams) == 2
        assert all(isinstance(stream, AbstractStream)
                   for stream in stream._streams.values())
        assert stream._streams['stream1'].rate_manager.loop_rate == 120
        assert stream._streams['stream2'].rate_manager.loop_rate == 60

    def test_compile(self, compose_stream: CustomComposeStream):
        assert not compose_stream.compiled()
        assert not compose_stream._compiled
        assert compose_stream.name.startswith('CustomComposeStream-')
        assert compose_stream.name == compose_stream.logger.name
        assert all([not stream.compiled()
                    for stream in compose_stream._streams.values()])
        compose_stream.compile()
        assert compose_stream.compiled()
        assert compose_stream._compiled
        assert compose_stream.name == 'CustomComposeStream'
        assert compose_stream.logger.name == 'CustomComposeStream'
        assert all([stream.compiled()
                    for stream in compose_stream._streams.values()])

    def test_substreams_loop_rate(self, compose_stream):
        compose_stream.start()
        compose_stream.wait(timeout=3.0)
        stream1 = compose_stream._streams['stream1']
        stream2 = compose_stream._streams['stream2']

        assert pytest.approx(stream1.state.count1, rel=0.1) == 360
        assert pytest.approx(stream2.state.count2, rel=0.1) == 180

    def test_start(self, compose_stream: CustomComposeStream):
        assert compose_stream.stopped()
        assert all(not stream.compiled() for stream in compose_stream._streams.values())
        assert all(stream.stopped() for stream in compose_stream._streams.values())
        assert all(stream.joined() for stream in compose_stream._streams.values())
        compose_stream.start()
        assert not compose_stream.stopped()
        assert all(stream.compiled() for stream in compose_stream._streams.values())
        assert all(not stream.stopped() for stream in compose_stream._streams.values())
        assert all(not stream.joined() for stream in compose_stream._streams.values())

    def test_wait(self, compose_stream: CustomComposeStream, time_meter):
        compose_stream.start()
        time_meter.start()
        compose_stream.wait(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, abs=0.05) == 0.1

    def test_stop(self, compose_stream: CustomComposeStream):
        compose_stream.start()
        compose_stream.wait(timeout=0.01)
        assert not compose_stream.stopped()
        assert all(not stream.stopped() for stream in compose_stream._streams.values())
        compose_stream.stop()
        assert compose_stream.stopped()
        assert all(stream.stopped() for stream in compose_stream._streams.values())

    def test_join(self, compose_stream: CustomComposeStream):
        compose_stream.start()
        compose_stream.wait(timeout=0.01)
        compose_stream.stop()
        assert not compose_stream.joined()
        assert all(stream.stopped() for stream in compose_stream._streams.values())
        assert all(not stream.joined() for stream in compose_stream._streams.values())
        compose_stream.join()
        assert compose_stream.joined()
        assert all(stream.stopped() for stream in compose_stream._streams.values())
        assert all(stream.joined() for stream in compose_stream._streams.values())

    def test_join_timeout(self):
        class TimeoutStream(ThreadStream):
            def work(self):
                time.sleep(1)

        class TimeoutComposeStream(ComposeStream):
            def __init__(self):
                super().__init__()
                self.state = CountState()
                self.timeout_stream = TimeoutStream()
                self.stream1 = CustomStream1(self.state)
                self.stream2 = CustomStream2(self.state)

        compose_stream = TimeoutComposeStream()
        compose_stream.start()
        compose_stream.wait(timeout=0.01)
        compose_stream.stop()
        assert not compose_stream.joined()
        compose_stream.join(timeout=0.1)
        assert not compose_stream.joined()
        compose_stream.join(timeout=1)
        assert compose_stream.joined()
