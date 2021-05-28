import sys
import logging


def setup_logger(name):
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')
    stdout = logging.StreamHandler(stream=sys.stdout)
    stdout.setLevel(logging.INFO)
    stdout.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(stdout)
    return logger
