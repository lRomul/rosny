from queue import Queue

from rosny import ThreadStream, ComposeStream


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
        super().__init__()
        self.queue = queue

    def work(self):
        value = self.queue.get(timeout=1)
        self.logger.info(f'{value}')


class MainStream(ComposeStream):
    def __init__(self):
        super().__init__()
        queue = Queue()
        self.sender = SenderStream(queue)
        self.receiver = ReceiverStream(queue)


if __name__ == "__main__":
    stream = MainStream()
    stream.start()
    stream.wait(10)
    stream.stop()
    stream.join()
