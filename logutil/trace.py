import functools
import inspect
import sys
import traceback
    

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
                msg = errno_message_map.get(errno_or_msg) or errno_or_msg
                line = Trace.file(Trace._caller_stack())
                getattr(logger, log_level.lower())(line + ':\n' + message)
                if throws:
                    raise
            except:
                logger.error(traceback.format_exc().decode(sys.getfilesystemencoding()))
                if throws:
                    raise
        return function_invoker
    return function_wrapper


class Trace:
    @staticmethod
    def _caller_stack(pointer=2):
        return inspect.stack()[pointer]

    @staticmethod
    def cls(caller_stack=None):
        try:
            stack = caller_stack or Trace._caller_stack()
            cls = stack[0].f_locals['self'].__class__
            return cls.__module__ + '.' + cls.__name__
        except KeyError:
            return AssertionError('outside of context, no class object')

    @staticmethod
    def method(caller_stack=None):
        try:
            stack = caller_stack or Trace._caller_stack()
            cls = stack[0].f_locals['self'].__class__
            return cls.__module__ + '.' + cls.__name__ + '.' + stack[3]
        except KeyError:
            return AssertionError('outside of context, no class object')

    @staticmethod
    def module(caller_stack=None):
        stack = caller_stack or Trace._caller_stack()
        return stack[0].f_globals.get('__name__')

    @staticmethod
    def func(caller_stack=None):
        stack = caller_stack or Trace._caller_stack()
        if stack[3] == '<module>':
            return AssertionError('outside of context, no function object')
        return stack[0].f_globals.get('__name__') + '.' + stack[3]

    @staticmethod
    def file(caller_stack=None):
        stack = caller_stack or Trace._caller_stack()
        ns = stack[0].f_globals.get('__name__')
        return "%s" % stack[1]


class Traceable(object):
    __clsname__ = 'Traceable'

    def this(self):
        return u"{ns}.{obj}".format(ns=self.__class__.__module__, obj=self.__class__.__name__, )

    @classmethod
    def base(cls, level=0):
        cls = cls.__base__ if (level == 0) else cls
        if cls.__base__ == object:
            raise AssertionError("There are no any class objects has the attribute: '__clsname__'")

        attr_name = '_' + cls.__name__ + '__clsname__'
        if hasattr(cls, attr_name):
            return u"{ns}.{obj}".format(ns=cls.__module__, obj=getattr(cls, attr_name), )
        return cls.__base__.base(level + 1)
