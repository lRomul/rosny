from rosny.abstract import AbstractStream
from rosny.loop import LoopStream


def test_abstract_stream(monkeypatch):
    monkeypatch.setattr(AbstractStream, '__abstractmethods__', set())

    class MockAbstractStream(AbstractStream):
        pass

    stream = MockAbstractStream()
    assert stream.compile() is None
    assert stream.start() is None
    assert stream.wait() is None
    assert stream.stop() is None
    assert stream.join() is None
    assert stream.compiled() is None
    assert stream.stopped() is None
    assert stream.joined() is None


def test_loop_stream(monkeypatch):
    monkeypatch.setattr(LoopStream, '__abstractmethods__', set())

    class MockLoopStream(LoopStream):
        pass

    stream = MockLoopStream()
    assert stream.work() is None
    assert stream._start_driver() is None
    assert stream._stop_driver() is None
    assert stream._join_driver(None) is None
