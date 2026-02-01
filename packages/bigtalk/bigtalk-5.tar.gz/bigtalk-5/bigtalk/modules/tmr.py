# This file is placed in the Public Domain.


import logging
import random
import threading
import time


from bigtalk.defines import Broker, Dict, Disk, Locate, Methods, Object
from bigtalk.defines import NoDate, Time, Timed


rand = random.SystemRandom()


def init():
    Timers.path = Locate.last(Timers.timers) or Methods.ident(Timers.timers)
    remove = []
    for tme, args in Dict.items(Timers.timers):
        if not args:
            continue
        orig, channel, txt = args
        for origin in Broker.like(orig):
            if not origin:
                continue
            diff = float(tme) - time.time()
            if diff > 0:
                bot = Broker.get(origin)
                timer = Timed(diff, bot.say, channel, txt)
                timer.start()
            else:
                remove.append(tme)
    for tme in remove:
        Timers.delete(tme)
    if Timers.timers:
        Disk.write(Timers.timers, Timers.path)
    logging.warning("%s timers", len(Timers.timers))


class Timer(Object):

    pass


class Timers(Object):

    path = ""
    timers = Timer()
    lock = threading.RLock()
    
    @staticmethod
    def add(tme, orig, channel,  txt):
        with Timers.lock:
            setattr(Timers.timers, str(tme), (orig, channel, txt))

    @staticmethod
    def delete(tme):
        with Timers.lock:
            delattr(Timers.timers, str(tme))


def tmr(event):
    result = ""
    if not event.rest:
        nmr = 0
        for tme, txt in Dict.items(Timers.timers):
            lap = float(tme) - time.time()
            if lap > 0:
                event.reply(f'{nmr} {" ".join(txt)} {Time.elapsed(lap)}')
                nmr += 1
        if not nmr:
            event.reply("no timers.")
        return result
    seconds = 0
    line = ""
    for word in event.args:
        if word.startswith("+"):
            try:
                seconds = int(word[1:])
            except (ValueError, IndexError):
                event.reply(f"{seconds} is not an integer")
                return result
        else:
            line += word + " "
    if seconds:
        target = time.time() + seconds
    else:
        try:
            target = Time.day(event.rest)
        except NoDate:
            target = Time.extract(Time.today())
        hours =  Time.hour(event.rest)
        if hours:
            target += hours
    target += rand.random() 
    if not target or time.time() > target:
        event.reply("already passed given time.")
        return result
    diff = target - time.time()
    txt = " ".join(event.args[1:])
    Timers.add(target, event.orig, event.channel, txt)
    Disk.write(Timers.timers, Timers.path or Methods.ident(Timers.timers))
    bot = Broker.get(event.orig)
    timer = Timed(diff, bot.say, event.orig, event.channel, txt)
    timer.start()
    event.reply("ok " + Time.elapsed(diff))
