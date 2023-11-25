import os
import multiprocessing
from multiprocessing import Queue

from rosny import ThreadNode, ProcessNode, ComposeNode


class SenderNode(ThreadNode):  # using threading.Thread
    def __init__(self, queue: Queue):
        super().__init__(loop_rate=30)
        self.queue = queue
        self.count = 0

    # run the method in a loop in a separate thread
    def work(self):
        self.queue.put(self.count)
        self.logger.info(f'pid {os.getpid()}, put {self.count}')
        self.count += 1


class ReceiverNode(ProcessNode):  # using multiprocessing.Process
    def __init__(self, queue: Queue):
        super().__init__(profile_interval=3)
        self.queue = queue

    # run the method in a loop in a separate process
    def work(self):
        value = self.queue.get(timeout=1)
        self.logger.info(f'pid {os.getpid()}, get {value}')


class MainNode(ComposeNode):  # merging several nodes
    def __init__(self):
        super().__init__()
        queue = Queue()
        self.sender = SenderNode(queue)
        self.receiver = ReceiverNode(queue)
        self.compile()
        self.logger.info(f'pid {os.getpid()}, init')


if __name__ == "__main__":
    """
    Method of processes starting that available on Unix, Windows, and macOS.
    You can use any method available on your OS
    https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    """
    multiprocessing.set_start_method('spawn')

    node = MainNode()
    node.start()
    node.wait(12)
    node.stop()
    node.join()
