from rosny.abstract import AbstractNode
from rosny.loop import LoopNode


def test_abstract_node(monkeypatch):
    monkeypatch.setattr(AbstractNode, '__abstractmethods__', set())

    class MockAbstractNode(AbstractNode):
        pass

    node = MockAbstractNode()
    assert node.compile() is None
    assert node.start() is None
    assert node.wait() is None
    assert node.stop() is None
    assert node.join() is None
    assert node.compiled() is None
    assert node.stopped() is None
    assert node.joined() is None


def test_loop_node(monkeypatch):
    monkeypatch.setattr(LoopNode, '__abstractmethods__', set())

    class MockLoopNode(LoopNode):
        pass

    node = MockLoopNode()
    assert node.work() is None
    assert node._start_driver() is None
    assert node._stop_driver() is None
    assert node._join_driver(None) is None
