import multiprocessing
from queue import Queue

from rosny import CommonState, ThreadNode, ProcessNode, ComposeNode


class State(CommonState):
    def __init__(self):
        super(State, self).__init__()
        self.value = multiprocessing.Value("i", 0)


class SenderNode(ThreadNode):
    def __init__(self, queue: Queue):
        super().__init__(loop_rate=30)
        self.queue = queue
        self.count = 0

    def work(self):
        self.queue.put(self.count)
        self.count += 1


class ReceiverNode(ThreadNode):
    def __init__(self, queue: Queue):
        super().__init__(profile_interval=3)
        self.queue = queue

    def work(self):
        self.common_state.value.value = self.queue.get(timeout=1)


class MultiThreadNode(ComposeNode):
    def __init__(self):
        super().__init__()
        queue = Queue()
        self.sender = SenderNode(queue)
        self.receiver = ReceiverNode(queue)


class InProcessNode(ProcessNode):
    node: MultiThreadNode

    def on_loop_begin(self):
        self.node = MultiThreadNode()
        self.node.compile(common_state=self.common_state,
                          name=f"{self.name}/node",
                          handle_signals=False)
        self.node.start()

    def work(self):
        self.node.wait(timeout=1)

    def on_loop_end(self):
        self.node.stop()
        self.node.join()


if __name__ == "__main__":
    node = InProcessNode()
    state = State()
    node.compile(common_state=state)
    node.start()
    node.wait(10)
    node.stop()
    node.join()
    print("Counter", state.value.value)
