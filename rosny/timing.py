import time


class LoopTimeMeter:
    def __init__(self):
        self.mean = 0.0
        self.count = 0
        self.restart_time = time.perf_counter()
        self.prev_time = self.restart_time

    def start(self):
        self.prev_time = time.perf_counter()

    def end(self):
        self.count += 1
        now_time = time.perf_counter()
        delta = now_time - self.prev_time
        self.mean += (delta - self.mean) / self.count
        self.prev_time = now_time

    def reset(self):
        self.mean = 0.0
        self.count = 0
        self.restart_time = time.perf_counter()
