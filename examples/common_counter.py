import time
import random
from threading import Lock

from rosny import ThreadStream, ComposeStream


class Counter:
    def __init__(self):
        self.count = 0


class CountStream(ThreadStream):
    def __init__(self, counter: Counter):
        super().__init__(loop_rate=10)
        self.counter = counter
        self.lock = Lock()

    def work(self):
        time.sleep(random.random() / 10)
        with self.lock:
            self.counter.count += 1
            self.logger.info(f'{self.counter.count}')


class MainStream(ComposeStream):
    def __init__(self):
        super().__init__()
        counter = Counter()
        self.stream0 = CountStream(counter)
        self.stream1 = CountStream(counter)
        self.stream2 = CountStream(counter)
        self.stream3 = CountStream(counter)
        self.stream4 = CountStream(counter)
        self.stream5 = CountStream(counter)
        self.stream6 = CountStream(counter)
        self.stream7 = CountStream(counter)
        self.stream8 = CountStream(counter)
        self.stream9 = CountStream(counter)


if __name__ == "__main__":
    stream = MainStream()
    stream.start()
    stream.wait(60)
    stream.stop()
    stream.join()
