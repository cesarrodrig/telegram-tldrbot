import logging

from config import LOGGING_LEVEL

loggers = {}

def get_logger(name):
    global loggers

    if name in loggers:
        return loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_LEVEL)

    formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s: %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    loggers[name] = logger

    return logger
