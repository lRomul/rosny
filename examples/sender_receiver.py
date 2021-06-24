import os
from multiprocessing import Queue
from rosny import ThreadStream, ProcessStream, ComposeStream


class SenderStream(ThreadStream):  # using threading.Thread
    def __init__(self, queue: Queue):
        super().__init__(loop_rate=30)
        self.queue = queue
        self.count = 0

    # run the method in a loop in a separate process
    def work(self):
        self.queue.put(self.count)
        self.logger.info(f'{os.getpid()}: put {self.count}')
        self.count += 1


class ReceiverStream(ProcessStream):  # using multiprocessing.Process
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    # run the method in a loop in a separate process
    def work(self):
        value = self.queue.get(timeout=1)
        self.logger.info(f'{os.getpid()}: get {value}')


class MainStream(ComposeStream):
    def __init__(self):
        super().__init__()
        queue = Queue()
        self.sender = SenderStream(queue)
        self.receiver = ReceiverStream(queue)
        self.logger.info(f'{os.getpid()}: init')


if __name__ == "__main__":
    stream = MainStream()
    stream.start()
    stream.wait(5)
    stream.stop()
    stream.join()
