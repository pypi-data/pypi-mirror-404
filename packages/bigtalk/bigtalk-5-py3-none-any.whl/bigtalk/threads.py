# This file is placed in the Public Domain.


"make it non-blocking"


import inspect
import logging
import queue
import threading
import time
import _thread


lock = threading.RLock()


"thread"


class Task(threading.Thread):

    def __init__(self, func, *args, daemon=True, **kwargs):
        super().__init__(None, self.run, None, (), daemon=daemon)
        self.event = None
        self.name = kwargs.get("name", Thread.name(func))
        self.queue = queue.Queue()
        self.result = None
        self.starttime = time.time()
        self.stopped = threading.Event()
        self.queue.put((func, args))

    def __iter__(self):
        return self

    def __next__(self):
        yield from dir(self)

    def join(self, timeout=0.0):
        "join thread and return result."
        try:
            super().join(timeout or None)
            return self.result
        except (KeyboardInterrupt, EOFError) as ex:
            if self.event:
                self.event.ready()
            raise ex

    def run(self):
        "run function."
        func, args = self.queue.get()
        if args and hasattr(args[0], "ready"):
            self.event = args[0]
        try:
            self.result = func(*args)
        except (KeyboardInterrupt, EOFError):
            if self.event:
                self.event.ready()
            _thread.interrupt_main()
        except Exception as ex:
            if self.event:
                self.event.ready()
            logging.exception(ex)
            _thread.interrupt_main()


class Thread:

    @staticmethod
    def launch(func, *args, **kwargs):
        "run function in a thread."
        with lock:
            try:
                thread = Task(func, *args, **kwargs)
                thread.start()
                return thread
            except (KeyboardInterrupt, EOFError):
                _thread.interrupt_main()

    @staticmethod
    def name(obj):
        "string of function/method."
        if inspect.ismethod(obj):
            return f"{obj.__self__.__class__.__name__}.{obj.__name__}"
        if inspect.isfunction(obj):
            return repr(obj).split()[1]
        return repr(obj)


"interface"


def __dir__():
    return (
        'Thread',
    )
