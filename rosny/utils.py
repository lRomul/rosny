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
