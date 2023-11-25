[![ROSNY](logo/rosny_logo_bg.svg)](https://lromul.github.io/rosny/)

rosny is a lightweight library for building concurrent systems.

## Installation

Tested on:

* Linux
* Python >= 3.8

From pip:

```bash
pip install rosny
```

From source:

```bash
pip install git+https://github.com/lRomul/rosny.git@master
```

## Example

```python
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
        self.logger.info(f'put {self.count}')
        self.count += 1


class ReceiverNode(ProcessNode):  # using multiprocessing.Process
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    # run the method in a loop in a separate process
    def work(self):
        value = self.queue.get(timeout=1)
        self.logger.info(f'get {value}')


class MainNode(ComposeNode):  # merging several nodes
    def __init__(self):
        super().__init__()
        queue = Queue()
        self.sender = SenderNode(queue)
        self.receiver = ReceiverNode(queue)


if __name__ == "__main__":
    node = MainNode()
    node.start()
    node.wait(5)
    node.stop()
    node.join()
```
