import time
import pytest

from rosny import ThreadNode, ComposeNode
from rosny.abstract import AbstractNode


class CountState:
    def __init__(self):
        self.count1 = 0
        self.count2 = 0


class CustomNode1(ThreadNode):
    def __init__(self, state):
        super().__init__(loop_rate=120)
        self.state = state

    def work(self):
        self.state.count1 += 1


class CustomNode2(ThreadNode):
    def __init__(self, state):
        super().__init__(loop_rate=60)
        self.state = state

    def work(self):
        self.state.count2 += 1


class CustomComposeNode(ComposeNode):
    def __init__(self):
        super().__init__()
        self.state = CountState()
        self.node1 = CustomNode1(self.state)
        self.node2 = CustomNode2(self.state)


@pytest.fixture(scope='function')
def compose_node():
    node = CustomComposeNode()
    yield node
    node.stop()
    node.join()


class TestBaseComposeNode:
    def test_init(self):
        node = CustomComposeNode()
        assert node.name.startswith('CustomComposeNode-')
        assert isinstance(node.state, CountState)
        assert len(node._nodes) == 2
        assert all(isinstance(node, AbstractNode)
                   for node in node._nodes.values())
        assert node._nodes['node1'].rate_manager.loop_rate == 120
        assert node._nodes['node2'].rate_manager.loop_rate == 60

    def test_compile(self, compose_node: CustomComposeNode):
        assert not compose_node.compiled()
        assert not compose_node._compiled
        assert compose_node.name.startswith('CustomComposeNode-')
        assert compose_node.name == compose_node.logger.name
        assert all([not node.compiled()
                    for node in compose_node._nodes.values()])
        compose_node.compile()
        assert compose_node.compiled()
        assert compose_node._compiled
        assert compose_node.name == 'CustomComposeNode'
        assert compose_node.logger.name == 'CustomComposeNode'
        assert all([node.compiled()
                    for node in compose_node._nodes.values()])

    def test_subnodes_loop_rate(self, compose_node):
        compose_node.start()
        compose_node.wait(timeout=3.0)
        node1 = compose_node._nodes['node1']
        node2 = compose_node._nodes['node2']

        assert pytest.approx(node1.state.count1, rel=0.1) == 360
        assert pytest.approx(node2.state.count2, rel=0.1) == 180

    def test_start(self, compose_node: CustomComposeNode):
        assert compose_node.stopped()
        assert all(not node.compiled() for node in compose_node._nodes.values())
        assert all(node.stopped() for node in compose_node._nodes.values())
        assert all(node.joined() for node in compose_node._nodes.values())
        compose_node.start()
        assert not compose_node.stopped()
        assert all(node.compiled() for node in compose_node._nodes.values())
        assert all(not node.stopped() for node in compose_node._nodes.values())
        assert all(not node.joined() for node in compose_node._nodes.values())

    def test_wait(self, compose_node: CustomComposeNode, time_meter):
        compose_node.start()
        time_meter.start()
        compose_node.wait(timeout=0.1)
        time_meter.end()
        assert pytest.approx(time_meter.mean, abs=0.05) == 0.1

    def test_stop(self, compose_node: CustomComposeNode):
        compose_node.start()
        compose_node.wait(timeout=0.01)
        assert not compose_node.stopped()
        assert all(not node.stopped() for node in compose_node._nodes.values())
        compose_node.stop()
        assert compose_node.stopped()
        assert all(node.stopped() for node in compose_node._nodes.values())

    def test_join(self, compose_node: CustomComposeNode):
        compose_node.start()
        compose_node.wait(timeout=0.01)
        compose_node.stop()
        assert not compose_node.joined()
        assert all(node.stopped() for node in compose_node._nodes.values())
        assert all(not node.joined() for node in compose_node._nodes.values())
        compose_node.join()
        assert compose_node.joined()
        assert all(node.stopped() for node in compose_node._nodes.values())
        assert all(node.joined() for node in compose_node._nodes.values())

    def test_join_timeout(self):
        class TimeoutNode(ThreadNode):
            def work(self):
                time.sleep(1)

        class TimeoutComposeNode(ComposeNode):
            def __init__(self):
                super().__init__()
                self.state = CountState()
                self.timeout_node = TimeoutNode()
                self.node1 = CustomNode1(self.state)
                self.node2 = CustomNode2(self.state)

        compose_node = TimeoutComposeNode()
        compose_node.start()
        compose_node.wait(timeout=0.01)
        compose_node.stop()
        assert not compose_node.joined()
        compose_node.join(timeout=0.1)
        assert not compose_node.joined()
        compose_node.join(timeout=1)
        assert compose_node.joined()
