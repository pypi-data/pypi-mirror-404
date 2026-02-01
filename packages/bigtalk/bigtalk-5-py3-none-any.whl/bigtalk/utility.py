# This file is placed in the Public Domain.


"usefulness"


import datetime
import inspect
import logging
import os
import re
import threading
import time


from .threads import Thread


class NoDate(Exception):

    pass


"logging"


class Format(logging.Formatter):

    def format(self, record):
        record.module = record.module.upper()
        return logging.Formatter.format(self, record)


class Log:

    datefmt = "%H:%M:%S"
    format = "%(module).3s %(message)s"

    @staticmethod
    def level(loglevel):
        "set log level."
        formatter = Format(Log.format, Log.datefmt)
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logging.basicConfig(
            level=loglevel.upper(),
            handlers=[stream,],
            force=True
        )


"repeater"


class Timy(threading.Timer):

    def __init__(self, sleep, func, *args, **kwargs):
        super().__init__(sleep, func)
        self.name = kwargs.get("name", Thread.name(func))
        self.sleep = sleep
        self.state = {}
        self.state["latest"] = time.time()
        self.state["starttime"] = time.time()
        self.starttime = time.time()


class Timed:

    def __init__(self, sleep, func, *args, thrname="", **kwargs):
        self.args = args
        self.func = func
        self.kwargs = kwargs
        self.sleep = sleep
        self.name = thrname or kwargs.get("name", Thread.name(func))
        self.target = time.time() + self.sleep
        self.timer = None

    def run(self):
        "run timed function."
        self.timer.latest = time.time()
        self.func(*self.args)

    def start(self):
        "start timer."
        self.kwargs["name"] = self.name
        timer = Timy(self.sleep, self.run, *self.args, **self.kwargs)
        timer.start()
        self.timer = timer

    def stop(self):
        "stop timer."
        if self.timer:
            self.timer.cancel()


class Repeater(Timed):

    def run(self):
        "run function and launch timer for next run."
        Thread.launch(self.start)
        super().run()


"time"


class Time:

    @staticmethod
    def date(daystr):
        "date from string."
        daystr = daystr.encode('utf-8', 'replace').decode("utf-8")
        res = time.time()
        for fmat in TIMES:
            try:
                res = time.mktime(time.strptime(daystr, fmat))
                break
            except ValueError:
                pass
        return res

    @staticmethod
    def day(daystr):
        "day part in a string."
        days = None
        month = None
        yea = None
        try:
            ymdre = re.search(r'(\d+)-(\d+)-(\d+)', daystr)
            if ymdre:
                (days, month, yea) = ymdre.groups()
        except ValueError:
            try:
                ymre = re.search(r'(\d+)-(\d+)', daystr)
                if ymre:
                    (days, month) = ymre.groups()
                    yea = time.strftime("%Y", time.localtime())
            except Exception as ex:
                raise NoDate(daystr) from ex
        if days:
            days = int(days)
            month = int(month)
            yea = int(yea)
            dte = f"{days} {MONTH[month]} {yea}"
            return time.mktime(time.strptime(dte, r"%d %b %Y"))
        raise NoDate(daystr)

    @staticmethod
    def elapsed(seconds, short=True):
        "seconds to string."
        txt = ""
        nsec = float(seconds)
        if nsec < 1:
            return f"{nsec:.2f}s"
        yea     = 365 * 24 * 60 * 60
        week    = 7 * 24 * 60 * 60
        nday    = 24 * 60 * 60
        hou    = 60 * 60
        minute  = 60
        yeas    = int(nsec / yea)
        nsec   -= yeas * yea
        weeks   = int(nsec / week)
        nsec   -= weeks * week
        nrdays  = int(nsec / nday)
        nsec   -= nrdays * nday
        hours   = int(nsec / hou)
        nsec   -= hours * hou
        minutes = int(nsec / minute)
        nsec   -= minutes * minute
        sec     = int(nsec / 1)
        nsec   -= nsec - sec
        if yeas:
            txt += f"{yeas}y"
        if weeks:
            nrdays += weeks * 7
        if nrdays:
            txt += f"{nrdays}d"
        if hours:
            txt += f"{hours}h"
        if short and txt:
            return txt.strip()
        if minutes:
            txt += f"{minutes}m"
        if sec:
            txt += f"{sec}s"
        txt = txt.strip()
        return txt

    @staticmethod
    def extract(daystr):
        "extract date/time from string."
        previous = ""
        line = ""
        daystr = str(daystr)
        res = None
        for word in daystr.split():
            line = previous + " " + word
            previous = word
            try:
                res = Time.date(line.strip())
                break
            except ValueError:
                res = None
            line = ""
        return res

    @staticmethod
    def fntime(daystr):
        "time from path."
        datestr = " ".join(daystr.split(os.sep)[-2:])
        datestr = datestr.replace("_", " ")
        if "." in datestr:
            datestr, rest = datestr.rsplit(".", 1)
        else:
            rest = ""
        timd = time.mktime(time.strptime(datestr, "%Y-%m-%d %H:%M:%S"))
        if rest:
            timd += float("." + rest)
        return float(timd)

    @staticmethod
    def hour(daystr):
        "hour in string."
        try:
            hmsre = re.search(r'(\d+):(\d+):(\d+)', str(daystr))
            hours = 60 * 60 * (int(hmsre.group(1)))
            hoursmin = hours  + int(hmsre.group(2)) * 60
            hmsres = hoursmin + int(hmsre.group(3))
        except AttributeError:
            pass
        except ValueError:
            pass
        try:
            hmre = re.search(r'(\d+):(\d+)', str(daystr))
            hours = 60 * 60 * (int(hmre.group(1)))
            hmsres = hours + int(hmre.group(2)) * 60
        except AttributeError:
            return 0
        except ValueError:
            return 0
        return hmsres

    @staticmethod
    def timed(txt):
        "scan string for date/time."
        try:
            target = Time.day(txt)
        except NoDate:
            target = Time.extract(Time.today())
        hours = Time.hour(txt)
        if hours:
            target += hours
        return target

    @staticmethod
    def parsetxt(txt):
        "parse text for date/time."
        seconds = 0
        target = 0
        txt = str(txt)
        for word in txt.split():
            if word.startswith("+"):
                seconds = int(word[1:])
                return time.time() + seconds
            if word.startswith("-"):
                seconds = int(word[1:])
                return time.time() - seconds
        if not target:
            try:
                target = Time.day(txt)
            except NoDate:
                target = Time.extract(Time.today())
            hours = Time.hour(txt)
            if hours:
                target += hours
        return target

    @staticmethod
    def today():
        "start of the day."
        return str(datetime.datetime.today()).split()[0]


class Utils:

    @staticmethod
    def forever():
        "run forever until ctrl-c."
        while True:
            try:
                time.sleep(0.1)
            except (KeyboardInterrupt, EOFError):
                break

    @staticmethod
    def md5sum(path):
        "return md5 of a file."
        import hashlib
        with open(path, "r", encoding="utf-8") as file:
            txt = file.read().encode("utf-8")
            return hashlib.md5(txt, usedforsecurity=False).hexdigest()

    @staticmethod
    def pkgname(obj):
        "return package name of an object."
        return obj.__module__.split(".")[0]

    @staticmethod
    def pipxdir(name):
        "return examples directory."
        return f"~/.local/share/pipx/venvs/{name}/share/{name}/examples"

    @staticmethod
    def spl(txt):
        "list from comma seperated string."
        try:
            result = txt.split(",")
        except (TypeError, ValueError):
            result = []
        return [x for x in result if x]

    @staticmethod
    def where(obj):
        "path where object is defined."
        return os.path.dirname(inspect.getfile(obj))

    @staticmethod
    def wrapped(func):
        "wrap function in a try/except, silence ctrl-c/ctrl-d."
        try:
           func()
        except (KeyboardInterrupt, EOFError):
            pass


"data"


MONTH = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12
}


TIMES = [
    "%Y-%M-%D %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d-%m",
    "%m-%d"
]


"interface"


def __dir__():
    return (
        'Log',
        'NoDate',
        'Repeater',
        'Time',
        'Timed',
        'Utility'
    )