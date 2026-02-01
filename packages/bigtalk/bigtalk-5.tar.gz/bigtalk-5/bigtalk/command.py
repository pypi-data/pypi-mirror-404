# This file is placed in the Public Domain.


"write your own commands"


import inspect


from .brokers import Broker
from .message import Message
from .methods import Methods


"commands"


class Commands:

    cmds = {}
    names = {}

    @staticmethod
    def add(*args):
        "add functions to commands."
        for func in args:
            name = func.__name__
            Commands.cmds[name] = func
            Commands.names[name] = func.__module__.split(".")[-1]

    @staticmethod
    def command(evt):
        "command callback."
        Methods.parse(evt, evt.text)
        func = Commands.get(evt.cmd)
        if func:
            func(evt)
            bot = Broker.get(evt.orig)
            if bot:
                bot.display(evt)
        evt.ready()

    @staticmethod
    def cmd(text):
        "parse text for command and run it."
        for txt in text.split(" ! "):
            evt = Message()
            evt.text = txt
            evt.type = "command"
            Commands.command(evt)
            evt.wait()
        return evt

    @staticmethod
    def get(cmd):
        "get function for command."
        return Commands.cmds.get(cmd, None)

    @staticmethod
    def has(cmd):
        "whether cmd is registered."
        return cmd in Commands.cmds

    @staticmethod
    def scan(module):
        "scan a module for functions with event as argument."
        for key, cmdz in inspect.getmembers(module, inspect.isfunction):
            if 'event' not in inspect.signature(cmdz).parameters:
               continue
            Commands.add(cmdz)


"interface"


def __dir__():
    return (
        'Commands',
    )
