import logging

from config import LOGGING_LEVEL

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_LEVEL)

    formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s: %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger
