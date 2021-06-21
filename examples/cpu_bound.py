from rosny import ComposeStream, ThreadStream, ProcessStream
from rosny.timing import LoopTimeMeter


class CpuBoundThreadStream(ThreadStream):
    def __init__(self, number):
        super().__init__(min_sleep=0)
        self.number = number
        self.result = 0

    def work(self):
        self.result += self.number
        self.number -= 1
        if not self.number:
            raise Exception(str(self.result))


class MainThreadStream(ComposeStream):
    def __init__(self):
        super().__init__()
        self.stream1 = CpuBoundThreadStream(6_000_000)
        self.stream2 = CpuBoundThreadStream(6_000_000)
        self.stream3 = CpuBoundThreadStream(6_000_000)


class CpuBoundProcessStream(ProcessStream):
    def __init__(self, number):
        super().__init__(min_sleep=0)
        self.number = number
        self.result = 0

    def work(self):
        self.result += self.number
        self.number -= 1
        if not self.number:
            raise Exception(str(self.result))


class MainProcessStream(ComposeStream):
    def __init__(self):
        super().__init__()
        self.stream1 = CpuBoundProcessStream(6_000_000)
        self.stream2 = CpuBoundProcessStream(6_000_000)
        self.stream3 = CpuBoundProcessStream(6_000_000)


if __name__ == "__main__":
    time_meter = LoopTimeMeter()

    stream = MainThreadStream()
    stream.start()
    time_meter.start()
    stream.wait()
    time_meter.end()
    stream.stop()
    stream.join()
    print(f"Threading duration {time_meter.mean} seconds.")

    time_meter.reset()
    stream = MainProcessStream()
    stream.start()
    time_meter.start()
    stream.wait()
    time_meter.end()
    stream.stop()
    stream.join()
    print(f"Multiprocess duration {time_meter.mean} seconds.")
