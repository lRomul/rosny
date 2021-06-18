# rosny

[![PyPI version](https://badge.fury.io/py/rosny.svg)](https://badge.fury.io/py/rosny)
[![Test](https://github.com/lRomul/rosny/actions/workflows/test.yml/badge.svg)](https://github.com/lRomul/rosny/actions/workflows/test.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/lromul/rosny/badge)](https://www.codefactor.io/repository/github/lromul/rosny)
[![codecov](https://codecov.io/gh/lRomul/rosny/branch/master/graph/badge.svg?token=VPB9M1RAVP)](https://codecov.io/gh/lRomul/rosny)
[![Downloads](https://static.pepy.tech/personalized-badge/rosny?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/rosny)

rosny is a simple library for building concurrency systems.

## Installation

From pip:

```bash
pip install rosny
```

From source:

```bash
pip install -U git+https://github.com/lRomul/rosny.git@master
```

## Example

```python
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
```
