# This file is placed in the Public Domain.


"a callback engine as handler"


import logging
import queue
import threading
import _thread


from .brokers import Broker
from .threads import Thread


"hnadler"


class Handler:

    def __init__(self):
        self.cbs = {}
        self.queue = queue.Queue()
        self.running = threading.Event()
        
    def callback(self, event):
        "run callback function with event."
        func = self.cbs.get(event.kind, None)
        if not func:
            event.ready()
            return
        name = event.text and event.text.split()[0]
        event._thr = Thread.launch(func, event, name=name)

    def loop(self):
        "event loop."
        while self.running.is_set():
            event = self.queue.get()
            if not event:
                break
            event.orig = repr(self)
            self.callback(event)
        
    def put(self, event):
        "put event on queue."
        self.queue.put(event)

    def register(self, kind, callback):
        "register callback."
        self.cbs[kind] = callback

    def start(self, daemon=True):
        "start event handler loop."
        self.running.set()
        Thread.launch(self.loop, daemon=daemon)

    def stop(self):
        "stop event handler loop."
        self.running.clear()
        self.queue.put(None)


"client"
    

class Client(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.iqueue = queue.Queue()
        self.olock = threading.RLock()
        self.silent = True
        self.stopped = threading.Event()
        Broker.add(self)

    def announce(self, text):
        "announce text to all channels."
        if not self.silent:
            self.raw(text)

    def display(self, event):
        "display event results."
        with self.olock:
            for tme in event.result:
                txt = event.result.get(tme)
                self.dosay(event.channel, txt)

    def dosay(self, channel, text):
        "say called by display."
        self.say(channel, text)

    def loop(self):
        "input loop."
        while True:
            event = self.poll()
            if not event or self.stopped.is_set():
                break
            event.orig = repr(self)
            self.callback(event)

    def poll(self):
        "return event."
        return self.iqueue.get()

    def put(self, event):
        self.iqueue.put(event)

    def raw(self, text):
        "raw output."

    def say(self, channel, text):
        "say text in channel."
        self.raw(text)


"console"


class Console(Client):

    def loop(self):
        "input loop."
        while True:
            event = self.poll()
            if not event or self.stopped.is_set():
                break
            event.orig = repr(self)
            self.callback(event)
            event.wait()

    def poll(self):
        "return event."
        return self.iqueue.get()


"buffered"


class Output(Client):

    def __init__(self):
        super().__init__()
        self.oqueue = queue.Queue()

    def output(self):
        "output loop."
        while True:
            event = self.oqueue.get()
            if event is None:
                self.oqueue.task_done()
                break
            self.display(event)
            self.oqueue.task_done()

    def start(self):
        "start output loop."
        super().start()
        Thread.launch(self.output)

    def stop(self):
        "stop output loop."
        super().stop()
        self.oqueue.put(None)

    def wait(self):
        "wait for output to finish."
        try:
            self.oqueue.join()
        except Exception as ex:
            logging.exception(ex)
            _thread.interrupt_main()


"interface"


def __dir__():
    return (
        'Client',
        'Console',
        'Handler',
        'Output'
    )
