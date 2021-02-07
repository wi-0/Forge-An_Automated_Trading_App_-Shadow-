import os
import datetime
import inspect
import logging.config
from cfg.config import *

mainLogger = logging.getLogger('main')


def updateLogFilePath():
    currentTime = datetime.datetime.now(tz=datetime.timezone.utc).strftime(format='%Y%m%d_%H%M%S')
    logFileHandler = CONFIG_LOGGING['handlers']['fileHandler']
    logFilePath = logFileHandler['filename']
    logFileHandler['filename'] = os.path.dirname(logFilePath) + '/' + currentTime + '.log'


class Logger(object):

    def __init__(self, qualName, level='debug'):
        logger = logging.getLogger(qualName)
        self.logger = getattr(logger, level)

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            self.logCall(func)
            result = func(*args, **kwargs)
            return result
        return wrapper

    def logCall(self, func):
        self.logger(f'Called {inspect.getmodule(func).__name__}:{func.__name__}')
