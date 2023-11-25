import time

from rosny import ComposeNode, ThreadNode, ProcessNode


class CpuBoundThreadNode(ThreadNode):
    def __init__(self, number):
        super().__init__(min_sleep=0)
        self.number = number

    def work(self):
        self.number -= 1
        if not self.number:
            self.common_state.set_exit()


class MainThreadNode(ComposeNode):
    def __init__(self):
        super().__init__()
        self.node1 = CpuBoundThreadNode(6_000_000)
        self.node2 = CpuBoundThreadNode(6_000_000)


class CpuBoundProcessNode(ProcessNode):
    def __init__(self, number):
        super().__init__(min_sleep=0)
        self.number = number

    def work(self):
        self.number -= 1
        if not self.number:
            self.common_state.set_exit()


class MainProcessNode(ComposeNode):
    def __init__(self):
        super().__init__()
        self.node1 = CpuBoundProcessNode(6_000_000)
        self.node2 = CpuBoundProcessNode(6_000_000)


if __name__ == "__main__":
    thread_node = MainThreadNode()
    thread_node.start()
    start_time = time.time()
    thread_node.wait()
    end_time = time.time()
    thread_node.stop()
    thread_node.join()
    print(f"Threading duration {end_time - start_time} seconds.")

    process_node = MainProcessNode()
    process_node.start()
    start_time = time.time()
    process_node.wait()
    end_time = time.time()
    process_node.stop()
    process_node.join()
    print(f"Multiprocess duration {end_time - start_time} seconds.")
