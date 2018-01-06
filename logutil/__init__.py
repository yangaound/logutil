import logging
import os
import threading
import time
from logging.handlers import MemoryHandler


__version__ = '1.0.0'


_lock = threading.Lock()
LoggerClass = logging.getLoggerClass()


# configuration for this module

#  Level for loggers
LOG_LEVEL = logging.INFO
# Format string for handlers
LOG_RECORD_FMT = "[%(levelname)s][%(asctime)s] - %(message)s"
#  time format used for generating the suffix of a filename
SUFFIX_FMT = '%Y-%m-%d'
# buffer size for memory loggers
CAPACITY = 128
# flush level for memory loggers
FLUSH_LEVEL = logging.ERROR
#  time interval for memory loggers (units: seconds)
FLUSH_INTERVAL = 120


def make_handler(filename=None, format=LOG_RECORD_FMT, capacity=1, flushInterval=FLUSH_INTERVAL, flushLevel=FLUSH_LEVEL):
    """Factory function that return  a new instance of `logging.FileHandler` or `_MemoryHandler`(with buffer) or 
    `logging.StreamHandler` according to the argument `capacity` and `filename`.

    :param filename: It will be passed to create a `logging.FileHandler` if its not None and the argument capacity <= 1 .
    :param format: Format string for handlers.
    :param capacity: It will be passed to create a `_MemoryHandler` if its value greater then 1.
    :param flushInterval: the argument of the `_MemoryHandler`.
    :param flushLevel: the argument of the `_MemoryHandler`.
    """
    if filename is None:
        handler = logging.StreamHandler(stream=sys.stdout)
    else:
        filename = os.path.abspath(filename)
        with _lock:
            if not os.path.exists(os.path.dirname(filename) or './'):
                os.makedirs(os.path.dirname(filename), )
        handler = logging.FileHandler(filename)
    handler.setFormatter(logging.Formatter(format))
    if capacity > 1:
        handler = _MemoryHandler(flushInterval, capacity=capacity, flushLevel=flushLevel, target=handler)
    return handler


class SimpleLogger(LoggerClass):
    """This class inherits ``logging.Logger`` or its derived class. When it instantiating, a `logging.FileHandler`
    using file named {filename} will be created. the argument `filename` will be used as this logger name if
    argument `name` is omitted.

    :param name:
        Optional argument, The name of this logger. `__name__` will be used if its omitted.
    :type format:
        `str`

    :param level:
        Optional argument, The level of this logger. 'INFO' will be assumed if its omitted.
    :type level:
        `str` = {"DEBUG"|"INFO"|"WARNING"|"CRITICAL"|"ERROR"} or
        `int` or `long` = {logging.DEBUG | logging.INFO | logging.WARNING | logging.CRITICAL | logging.ERROR}

    :param filename:
        Optional keyword argument it will be used to create a `logging.FileHandler`. if its omitted or None,
        create a `logging.StreamHandler` using `sys.stdout` as the underlying stream.
    :type filename:
        `basestring`

    :param format:
        Optional keyword argument; Format string for handlers` .
        Default value: "[%(levelname)s][%(asctime)s] - %(message)s"
    :type format:
       `str`

    E.g., Create and use SimpleLogger:
    >>> import logutil
    >>> # create a logger named 'log' and write messages to stdout
    >>> logger = logutil.SimpleLogger(name='log')
    >>> logger.info('msg')
        [INFO][2017-01-06 12:54:18,230] - msg
    >>>
    >>> # a file named 'error.log' will be created and write messages to it
    >>> logger = logutil.SimpleLogger(name='log', filename='error.log')
    >>> logger.info('msg')
    """

    def __init__(self, name=__name__, level='INFO', **handlerParams):
        LoggerClass.__init__(self, name, level.supper())
        self._handlerParams = handlerParams
        self._create_and_attache_handler()

    def _create_and_attache_handler(self):
        handler = make_handler(**self._handlerParams)
        self.addHandler(handler)

    def __del__(self):
        for h in self.handlers:
            h.close()
            self.removeHandler(h)


class TimedRotatingLogger(SimpleLogger):
    """This class inherits ``logutil.SimpleLogger`` and the argument `kwargs` will be passed directly to super class 
    as additional keyword arguments. This logger auto rotate file according to argument `suffixFmt`; a file named 
    "{filename}.%Y-%m-%d" will be created every dayat midnight by default.

    Note: this logger just maintains one handler, others clients added will be popped out when method 
    `._rotate_handler()` be called.

    :param name:
        Optional argument, The name of this logger. `__name__` will be used if its omitted.
    :type format:
        `str`

    :param level:
        Optional argument, The level of this logger. 'INFO' will be assumed if its omitted.
    :type level:
        `str` = {"DEBUG"|"INFO"|"WARNING"|"CRITICAL"|"ERROR"} or
        `int` or `long` = {logging.DEBUG | logging.INFO | logging.WARNING | logging.CRITICAL | logging.ERROR}

    :param filename:
        Optional keyword argument it will be used to create a `logging.FileHandler`. if its omitted or None,
        create a `logging.StreamHandler` using `sys.stdout` as the underlying stream.
    :type filename:
        `basestring`

    :param format:
        Optional keyword argument; Format string for handlers` .
        Default value: "[%(levelname)s][%(asctime)s] - %(message)s"
    :type format:
       `str`

    :param suffixFmt:
        Optional keyword argument. It will be used to call time.strftime(suffixFmt) to generate a suffix of full_filename,
        full_filename = filename + '.' + time.strftime(suffixFmt).
        Default value: "%Y-%m-%d", it means that files will be rotated every day at midnight.
    :type suffixFmt:
        `str`

    E.g., Create and use `TimedRotatingLogger`:
    >>> logger = TimedRotatingLogger(filename='error_log', suffixFmt='%S') # rotate file at each second
    >>> logger.info('msg')
    """

    def __init__(self,  name=__name__, level='INFO', **handlerParams):
        self._baseFilename = handlerParams.get('filename')
        self._suffixFmt = handlerParams.pop('suffixFmt', SUFFIX_FMT)
        self._suffix = time.strftime(self._suffixFmt)
        self._re_lock = threading.RLock()
        SimpleLogger.__init__(self, name, level, **handlerParams)

    def handle(self, record):
        """overwrite"""
        if self._suffix != time.strftime(self._suffixFmt):
            with self._re_lock:
                if self._suffix != time.strftime(self._suffixFmt):
                    self._suffix = time.strftime(self._suffixFmt)
                    self._rotate_handler()
        LoggerClass.handle(self, record)

    def _rotate_handler(self):
        """Removes the all handlers from this logger, and then rotate filename (new a `logging.FileHandler`
        which be attached to this logger)"""
        with self._re_lock:
            self.__del__()
            self._create_and_attache_handler()

    def _create_and_attache_handler(self):
        if self._baseFilename is not None:
            self._handlerParams['filename'] = self._baseFilename + '.' + self._suffix
        SimpleLogger._create_and_attache_handler(self)


class TimedRotatingMemoryLogger(TimedRotatingLogger):
    """This class inherits ``logutil.TimedRotatingLogger`` and the argument `kwargs` will be passed to
    super class as additional keyword arguments. This logger buffers messages; clients working threads 
    just need to push message to memory; a new thread named 'flusher' asynchronously flush buffer once 
    some condition be satisfied.

    Note: this logger just maintains one handler, others clients added will be popped out when method
    `._rotate_handler()` be called.

    :param name:
        Optional argument, The name of this logger. `__name__` will be used if its omitted.
    :type format:
        `str`

    :param level:
        Optional argument, The level of this logger. 'INFO' will be assumed if its omitted.
    :type level:
        `str` = {"DEBUG"|"INFO"|"WARNING"|"CRITICAL"|"ERROR"} or
        `int` or `long` = {logging.DEBUG | logging.INFO | logging.WARNING | logging.CRITICAL | logging.ERROR}

    :param filename:
        Optional keyword argument it will be used to create a `logging.FileHandler`. if its omitted or None,
        create a `logging.StreamHandler` using `sys.stdout` as the underlying stream.
    :type filename:
        `basestring`

    :param format:
        Optional keyword argument; Format string for handlers` .
        Default value: "[%(levelname)s][%(asctime)s] - %(message)s"
    :type format:
       `str`

    :param suffixFmt:
        Optional keyword argument. It will be used to call time.strftime(suffixFmt) to generate a suffix of full_filename,
        full_filename = filename + '.' + time.strftime(suffixFmt).
        Default value: "%Y-%m-%d", it means that files will be rotated every day at midnight.
    :type suffixFmt:
        `str`

    :param capacity:
        Optional keyword argument, default value: 100. Buffer size; if the buffering is full, the `_MemoryHandler`
        auto flush it.
    :type capacity:
        `int`

    :param flushInterval:
        Optional keyword argument, default: 120 second. Flush buffering if time.time() - theLastFlushTime > flushInterval.
    :type flushInterval:
        `int`

    :param flushLevel:
        Optional keyword argument, default: logging.ERROR. Flush buffering if the level of a logRecord greater then or
        equal to the argument flushLevel.
    :type flushLevel:
        `str` = {"DEBUG"|"INFO"|"WARNING"|"CRITICAL"|"ERROR"} or
        `int` = {logging.DEBUG | logging.INFO | logging.WARNING | logging.CRITICAL | logging.ERROR}
    """

    def __init__(self, name=__name__, level='INFO', **handlerParams):
        capacity = handlerParams.get('capacity') or CAPACITY
        flushInterval = handlerParams.get('flushInterval') or FLUSH_INTERVAL
        flushLevel = handlerParams.get('flushLevel') or FLUSH_LEVEL
        flushLevel = getattr(logging, flushLevel.upper()) if isinstance(flushLevel, basestring) else flushLevel
        handlerParams.update({
            'capacity': capacity,
            'flushInterval': flushInterval,
            'flushLevel': flushLevel,
        })
        TimedRotatingLogger.__init__(self, name, level, **handlerParams)

    def flush(self):
        """Ensure all log records in buffer has been flushed."""
        with self._re_lock:
            for h in self.handlers:
                h.flush()


class _MemoryHandler(MemoryHandler):
    def __init__(self, flushInterval, **kwargs):
        MemoryHandler.__init__(self, **kwargs)
        self.__flushInterval = flushInterval
        self.__lastFlushTime = time.time()
        self.__condition = threading.Condition()
        self.__flusher = None

    def shouldFlush(self, record):
        return MemoryHandler.shouldFlush(self, record) or (time.time() - self.__lastFlushTime > self.__flushInterval)\
               or (record.levelno >= self.flushLevel)

    def flush(self):
        with self.__condition:
            try:
                target, buffered, self.buffer = self.target, self.buffer, []
                self.__flusher = threading.Thread(target=self.__flush, args=(target, buffered,), name='flusher')
                self.__flusher.isDaemon() and self.__flusher.setDaemon(False)
                self.__flusher.start()
                self.__condition.wait(1.0)
            except Exception:
                self.buffer = buffered
                time.sleep(0.01)

    def __flush(self, target, buffered):
        with self.__condition:
            self.__condition.notifyAll()
        for record in buffered:
            target.handle(record)
        self.__lastFlushTime = time.time()

    def close(self):
        self.flush()
        if self.__flusher and self.__flusher.is_alive():
            self.__flusher.join()
        MemoryHandler.close(self)
        

import functools
import traceback 
import sys

from .trace import Trace


errno_message_map = {
}


def set_errno_message_map(dict):
    errno_message_map.update(dict)

    
class LogException(Exception):
    pass
    
    
def handle_exception(logger, throws=False):
    def function_wrapper(func):
        @functools.wraps(func)
        def function_invoker(*args, **kwagrs):
            try:
                return func(*args, **kwagrs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except LogException as (log_level, errno_or_msg):
                message = errno_message_map.get(errno_or_msg) or errno_or_msg
                getattr(logger, log_level.lower())(message)
                if throws:
                    raise
            except:
                logger.error(traceback.format_exc().decode(sys.getfilesystemencoding()))
                if throws:
                    raise
        return function_invoker
    return function_wrapper
