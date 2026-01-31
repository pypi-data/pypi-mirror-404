"""
Thread-safe decorators for PySide6.

This module provides decorators to safely execute PySide6 methods from non-Qt threads.
Based on the pattern from inputs_for_copilot/decorators_pyqt6_threadsafe.py.
"""

import functools
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Qt, Signal



class _basic_caller(QObject):
    runit=Signal(object)
    def __init__(self):
        super().__init__()
        self.runit.connect(self.run)
        
    def run(self,torun):
        torun()
           
basicCaller:_basic_caller=None
def InitializeThreadSafe():
    global basicCaller
    basicCaller=_basic_caller()
    

class _threadSafeObject(QObject):
    """
    Internal class: Don't use outside this module.
    
    Wrapper object that executes a function in the Qt thread.
    """
    runit=Signal()
    
    def __init__(self, func, args, kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.return_value = None
        self.done=False
        self.runit.connect(self.run)
        
    @QtCore.Slot()
    def run(self):
        """Execute the wrapped function."""
        self.return_value = self.func(*self.args, **self.kwargs)
        self.done=True


def threadSafeMethode(func):
    """
    Decorator for QObject Class methods.
    At call the method is invoked in the Qt Thread without blocking.
    """    
    def f(*args, **kwargs):
        self = args[0]
        if QtCore.QThread.currentThread() == self.thread():
            return func(*args, **kwargs)
        tso = _threadSafeObject(func, args, kwargs)
        
        tso.moveToThread(self.thread())
        QtCore.QMetaObject.invokeMethod(tso, 'run')
    return f


def threadSafeMethodeReturn(func):
    """
    Decorator for QObject Class methods.
    At call the method is invoked in the Qt Thread and waits for returned value.
    """    
    def f(*args, **kwargs):
        self = args[0]
        if QtCore.QThread.currentThread() == self.thread():
            return func(*args, **kwargs)
        tso = _threadSafeObject(func, args, kwargs)
        
        tso.moveToThread(self.thread())
        QtCore.QMetaObject.invokeMethod(tso, 'run', QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        return tso.return_value
    return f


def threadSafeInApp(func):
    """
    Decorator for Module level functions.
    At call the method is invoked in the Qt Thread without blocking.
    """    
    def f(*args, **kwargs):
        appt = QApplication.instance().thread()
        if QtCore.QThread.currentThread() == appt:
            return func(*args, **kwargs)
        tso = _threadSafeObject(func, args, kwargs)
        
        tso.moveToThread(appt)
        QtCore.QMetaObject.invokeMethod(tso, 'run',QtCore.Qt.ConnectionType.QueuedConnection)
    return f


def threadSafeInAppReturn(func):
    """
    Decorator for Module level functions.
    At call the method is invoked in the Qt Thread and waits for returned value.
    """    
    def f(*args, **kwargs):
        appt = QApplication.instance().thread()
        if QtCore.QThread.currentThread() == appt:
            return func(*args, **kwargs)
        tso = _threadSafeObject(func, args, kwargs)
        
        tso.moveToThread(appt)
        QtCore.QMetaObject.invokeMethod(tso, 'run', QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        return tso.return_value
    return f


def threadSafeInApp2(func):
    """
    Decorator for Module level functions.
    At call the method is invoked in the Qt Thread without blocking.
    This function need object Initialization but is safe with asyncio loop
    """    
    @functools.wraps(func)
    def f(*args, **kwargs):
        if basicCaller:
            basicCaller.runit.emit(lambda :func(*args,**kwargs))
        
    return f


# Alias for use in WebSocketClient handlers
# Use this decorator on methods that need to interact with PySide6 objects
run_in_qt_thread = threadSafeInApp2
