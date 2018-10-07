import logging
import time

from logging.handlers import TimedRotatingFileHandler

logger = None

inited = False

def Info(_log_str):
    logger.info(_log_str)
    print(_log_str)


def init_logger():
    global inited

    if inited:
        return

    inited = True

    global logger
    logFilePath = "log/info.log"
    logger = logging.getLogger("GeekCashGame")
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(logFilePath,
                                       when="d",
                                       interval=1,
                                       backupCount=7)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler.setFormatter(formatter)

    logger.addHandler(handler)


init_logger()