import sys
import logging


def default_object_name(object_: object) -> str:
    return f"{object_.__class__.__name__}-{str(id(object_))}"


def setup_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s')
    stdout = logging.StreamHandler(stream=sys.stdout)
    stdout.setLevel(logging.INFO)
    stdout.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(stdout)
    return logger


class MeanMeter:
    def __init__(self):
        self.mean: float = 0.0
        self.count: int = 0

    def reset(self):
        self.mean = 0.0
        self.count = 0

    def update(self, value: float, n: int = 1):
        self.count += n
        self.mean += (value - self.mean) / self.count


class EMAMeter:
    def __init__(self, alpha: float):
        self.alpha = alpha
        self.one_minus_alpha = 1 - alpha
        self.mean: float = 0.0
        self.count = 0

    def reset(self):
        self.mean = 0.0
        self.count = 0

    def update(self, value: float):
        if self.count:
            self.mean = self.alpha * value + self.one_minus_alpha * self.mean
        else:
            self.mean = value
        self.count += 1
