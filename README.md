# logutil
This package defines 3 classes which extend ``loging.Logger`` or its derived classes for application in logging and buffering messages as well as rotating filename.<br />
該package定義了3個類別， 用來擴充``loging.Logger``或其子類， 以實現寫訊息至檔案、緩存若干條訊息並自動刷訊息、旋轉檔案等應用。


### class ``logutil.Simpleogger``(name=`__name__`, level='INFO', **handlerParams)
This class inherits ``logging.Logger`` or its derived class. argument `name` and `level` will be passed directly to the supper class and the argument `handlerParams` will be used to create a appropriate handler for this logger. When it instantiating, create a `logging.FileHandler` if the keyword argument `filename` is present, otherwise create a `logging.StreamHandler` using `sys.stdout` as the underlying stream.
```
>>> import logutil
>>> # create a logger named 'log' and write messages to stdout
>>> logger = logutil.SimpleLogger(name='log')
>>> logger.info('msg')
[INFO][2017-01-06 12:54:18,230] - msg
>>>
>>> # a file named 'error.log' will be created and write messages to it
>>> logger = logutil.SimpleLogger(name='log', filename='error.log')
>>> logger.info('msg')
```

### class ``logutil.TimedRotatingLogger``(name=`__name__`, level='INFO', **handlerParams)
This class inherits ``logutil.SimpleLogger``. This logger auto rotate file according to argument `suffixFmt`. if the keyword argument `filename` is present, a file named `{filename}.%Y-%m-%d` will be created every day
at midnight by default.
```
>>> import logutil, time
>>> logger = logutil.TimedRotatingLogger(filename='error_log', suffixFmt='%S')  # file will be rotated each second
>>> logger.info('message in a file')
>>> time.sleep(1.1)
>>> logger.info('message in another file')
>>>
```

### class ``logutil.TimedRotatingMemoryLogger``(name=`__name__`, level='INFO', **handlerParams)
This class inherits ``logutil.TimedRotatingLogger`` and the argument `handlerParams` will be passed to super class as additional keyword arguments. This logger buffers messages; clients working threads just need to push message to memory; a new thread named 'flusher' asynchronously flush buffer once some condition be satisfied.
```
>>> import logutil, time
>>>
>>> # 1. condiction satisfied by capacity(buffering is full)
>>> logger = logutil.TimedRotatingMemoryLogger(capacity=3)  # specify filename to write to file
>>> logger.info('not flush')
>>> logger.info('not flush')
>>> logger.info('flush immediately because buffer is full')
[INFO][2018-01-06 13:18:39,621] - not flush
[INFO][2018-01-06 13:18:41,289] - not flush
[INFO][2018-01-06 13:18:50,584] - flush immediately because buffer is full
>>>
>>> # 2. condiction satisfied by message level(logRecord.levelno >= flushLevel)
>>> logger = logutil.TimedRotatingMemoryLogger(flushLevel='warning')
>>> logger.info("not flush since 'info' < flushLevel")
>>> logger.warning("flush immediately because 'warning' == flushLevel")
[INFO][2018-01-06 13:34:23,164] - not flush since 'info' < flushLevel
[WARNING][2018-01-06 13:34:30,492] - flush immediately because 'warning' == flushLevel
>>> logger.error("flush immediately since 'error' > flushLevel")
[ERROR][2018-01-06 13:34:44,282] - flush immediately since 'error' > flushLevel
>>>
>>> # 3. condiction satisfied by time interval
>>> logger = logutil.TimedRotatingMemoryLogger('error_log', flushInterval=5)      # 5 seconds
>>> logger.info("not flush")
>>> time.sleep(6)
>>> logger.info('flush immediately since long time no flush')
[INFO][2018-01-06 13:39:13,937] - not flush
[INFO][2018-01-06 13:39:19,940] - flush immediately since long time no flush
>>>

Note: Rotating filename logger just maintains one handler, others clients added will be poped out when the method 
`._rotate_handler()` be called. 
```
### Comparison of performance of three types of logger
```
>>> def logs(logger, loop):
...     import time
...     tick = time.time()
...     for i in xrange(loop):
...         logger.info(str(i))
...     print "cost: %s seconds, logger: %s" % (time.time() - tick, logger.__class__.__name__)
...
>>> import logutil
>>> log = logutil.SimpleLogger(filename='00.log')
>>> _log = logutil.TimedRotatingLogger(filename='11.log')
>>> __log = logutil.TimedRotatingMemoryLogger(filename='22.log', capacity=1024)
>>>
>>> logs(log, loop=200)
cost: 0.0160000324249 seconds, logger: SimpleLogger
>>> logs(_log, loop=200)
cost: 0.0160000324249 seconds, logger: TimedRotatingLogger
>>> logs(__log, loop=200)
cost: 0.00800013542175 seconds, logger: TimedRotatingMemoryLogger
>>>
```
