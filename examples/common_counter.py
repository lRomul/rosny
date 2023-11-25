import time
import random
from threading import Lock

from rosny import ThreadNode, ComposeNode


class Counter:
    def __init__(self):
        self.count = 0


class CountNode(ThreadNode):
    def __init__(self, counter: Counter):
        super().__init__(loop_rate=10)
        self.counter = counter
        self.lock = Lock()

    def work(self):
        time.sleep(random.random() / 10)
        with self.lock:
            self.counter.count += 1
            self.logger.info(f'{self.counter.count}')


class MainNode(ComposeNode):
    def __init__(self):
        super().__init__()
        counter = Counter()
        self.node0 = CountNode(counter)
        self.node1 = CountNode(counter)
        self.node2 = CountNode(counter)
        self.node3 = CountNode(counter)
        self.node4 = CountNode(counter)
        self.node5 = CountNode(counter)
        self.node6 = CountNode(counter)
        self.node7 = CountNode(counter)
        self.node8 = CountNode(counter)
        self.node9 = CountNode(counter)


if __name__ == "__main__":
    node = MainNode()
    node.start()
    node.wait(60)
    node.stop()
    node.join()
