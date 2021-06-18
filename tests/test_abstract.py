from rosny.abstract import AbstractStream


def test_abstract(monkeypatch):
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
