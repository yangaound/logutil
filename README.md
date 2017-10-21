# logutil
This package defines classes which extends ``loging.Logger`` or its's derived classes for applications.<br />
該package定義了3個類別， 用來擴充``loging.Logger``或其子類， 以實現更靈活的應用。


### class ``logutil.SimpleLogger``(filename, level='info', format="[%(levelname)s][%(asctime)s] - %(message)s", name=None)
This logger creates a file named {filename} and appends message into it. 
argument `filename` will be used if argument `name` is omitted.
```
>>> import logutil
>>> logger = logutil.SimpleLogger('error.log') 
>>> logger.info('message')                     
>>>
```

### class ``logutil.TimedRotatingLogger``(filename, suffixFmt='%Y-%m-%d', **kwargs)
This class inherits ``logutil.SimpleLogger`` and the argument `kwargs` will be passed directly to super class as additional keyword arguments. This logger auto rotate file according to argument `suffixFmt`; file named "{filename}.%Y-%m-%d" will be created every day
at midnight by default.
```
>>> import logutil, time
>>> logger = logutil.TimedRotatingLogger('error_log', suffixFmt='%S')  # file will be rotated each second
>>> logger.info('message in a file')
>>> time.sleep(1.1)
>>> logger.info('message in another file')
>>>
```

### class ``logutil.TimedRotatingMemoryLogger``(filename, capacity=100, flushInterval=120, flushLevel='ERROR', **kwargs)
This class inherits ``logutil.TimedRotatingLogger``.<br />
This logger buffers message untill a event driven to flush asynchronously in a new thread named 'flusher'; clients working threads just need to push message to memory. 

```
>>> import logutil, logging, time
>>>
>>> # 1. condiction satisfied by capacity(buffering is full)
>>> logger = logutil.TimedRotatingMemoryLogger('error_log', capacity=3)
>>> # add another handler for demo
>>> logger.addHandler(logutil._MemoryHandler(filename=None, target=logging.StreamHandler(), capacity=3)) 
>>> logger.info('not flush')
>>> logger.info('not flush')
>>> logger.info('flush immediately because buffer is full')
>>>
>>> # 2. condiction satisfied by message level(logRecord.levelno >= flushLevel)
>>> logger = logutil.TimedRotatingMemoryLogger('error_log', flushLevel='warning')
>>> logger.warning("flush immediately because 'warning' == flushLevel")  
>>> logger.info("not flush since 'info' < flushLevel")
>>> logger.error('flush immediately since 'error' > flushLevel")   
>>>
>>> # 3. condiction satisfied by time interval
>>> logger = logutil.TimedRotatingMemoryLogger('error_log', flushInterval=5)      # 5 seconds
>>> time.sleep(6)
>>> logger.info('flush immediately since long time no flush')
>>>

Note: Rotating logger just maintains one handler, others clients added will be poped out when the method 
`rotate_handler()` be called. 
```
