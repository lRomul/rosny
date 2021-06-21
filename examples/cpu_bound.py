import time

from rosny import ComposeStream, ThreadStream, ProcessStream


class CpuBoundThreadStream(ThreadStream):
    def __init__(self, number):
        super().__init__(min_sleep=0)
        self.number = number

    def work(self):
        self.number -= 1
        if not self.number:
            self._internal_state.set_exit()


class MainThreadStream(ComposeStream):
    def __init__(self):
        super().__init__()
        self.stream1 = CpuBoundThreadStream(6_000_000)
        self.stream2 = CpuBoundThreadStream(6_000_000)


class CpuBoundProcessStream(ProcessStream):
    def __init__(self, number):
        super().__init__(min_sleep=0)
        self.number = number

    def work(self):
        self.number -= 1
        if not self.number:
            self._internal_state.set_exit()


class MainProcessStream(ComposeStream):
    def __init__(self):
        super().__init__()
        self.stream1 = CpuBoundProcessStream(6_000_000)
        self.stream2 = CpuBoundProcessStream(6_000_000)


if __name__ == "__main__":
    thread_stream = MainThreadStream()
    thread_stream.start()
    start_time = time.time()
    thread_stream.wait()
    end_time = time.time()
    thread_stream.stop()
    thread_stream.join()
    print(f"Threading duration {end_time - start_time} seconds.")

    process_stream = MainProcessStream()
    process_stream.start()
    start_time = time.time()
    process_stream.wait()
    end_time = time.time()
    process_stream.stop()
    process_stream.join()
    print(f"Multiprocess duration {end_time - start_time} seconds.")
