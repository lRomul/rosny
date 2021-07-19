import multiprocessing
from queue import Queue

from rosny import CommonState, ThreadStream, ProcessStream, ComposeStream


class State(CommonState):
    def __init__(self):
        super(State, self).__init__()
        self.value = multiprocessing.Value("i", 0)


class SenderStream(ThreadStream):
    def __init__(self, queue: Queue):
        super().__init__(loop_rate=30)
        self.queue = queue
        self.count = 0

    def work(self):
        self.queue.put(self.count)
        self.count += 1


class ReceiverStream(ThreadStream):
    def __init__(self, queue: Queue):
        super().__init__(profile_interval=3)
        self.queue = queue

    def work(self):
        self.common_state.value.value = self.queue.get(timeout=1)


class MultiThreadStream(ComposeStream):
    def __init__(self):
        super().__init__()
        queue = Queue()
        self.sender = SenderStream(queue)
        self.receiver = ReceiverStream(queue)


class InProcessStream(ProcessStream):
    stream: MultiThreadStream

    def on_loop_begin(self):
        self.stream = MultiThreadStream()
        self.stream.compile(common_state=self.common_state,
                            name=f"{self.name}/stream",
                            handle_signals=False)
        self.stream.start()

    def work(self):
        self.stream.wait(timeout=1)

    def on_loop_end(self):
        self.stream.stop()
        self.stream.join()


if __name__ == "__main__":
    stream = InProcessStream()
    state = State()
    stream.compile(common_state=state)
    stream.start()
    stream.wait(10)
    stream.stop()
    stream.join()
    print("Counter", state.value.value)
