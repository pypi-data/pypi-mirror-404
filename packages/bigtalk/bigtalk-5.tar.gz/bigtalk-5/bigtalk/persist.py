# This file is placed in the Public Domain.


"persistence through storage"


import json
import os
import pathlib
import threading


from .methods import Methods
from .objects import Dict, Json, Object
from .utility import Time


lock = threading.RLock()


"cache"


class Cache:

    paths = {}

    @staticmethod
    def add(path, obj):
        "put object into cache."
        Cache.paths[path] = obj

    @staticmethod
    def get(path):
        "get object from cache."
        return Cache.paths.get(path, None)

    @staticmethod
    def sync(path, obj):
        "update cached object."
        try:
            Dict.update(Cache.paths[path], obj)
        except KeyError:
            Cache.add(path, obj)


"workdir"


class Workdir:

    wdr = ""

    @staticmethod
    def setwd(path):
        "enable writing to disk."
        Workdir.wdr = path
        Workdir.skel()

    @staticmethod
    def kinds():
        "show kind on objects in cache."
        return os.listdir(os.path.join(Workdir.wdr, "store"))

    @staticmethod
    def long(name):
        "expand to fqn."
        split = name.split(".")[-1].lower()
        res = name
        for names in Workdir.kinds():
            if split == names.split(".")[-1].lower():
                res = names
                break
        return res

    @staticmethod
    def pidfile(name):
        "write pidfile."
        filename = os.path.join(Workdir.wdr, f"{name}.pid")
        if os.path.exists(filename):
            os.unlink(filename)
        path2 = pathlib.Path(filename)
        path2.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as fds:
            fds.write(str(os.getpid()))

    @staticmethod
    def skel():
        "create directories."
        if not Workdir.wdr:
            return
        path = os.path.abspath(Workdir.wdr)
        workpath = os.path.join(path, "store")
        pth = pathlib.Path(workpath)
        pth.mkdir(parents=True, exist_ok=True)
        modpath = os.path.join(path, "mods")
        pth = pathlib.Path(modpath)
        pth.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def workdir():
        "return workdir."
        return Workdir.wdr


"disk"


class Disk:

    @staticmethod
    def read(obj, path):
        "read object from path."
        with lock:
            pth = os.path.join(Workdir.wdr, "store", path)
            with open(pth, "r", encoding="utf-8") as fpt:
                try:
                    Dict.update(obj, Json.load(fpt))
                except json.decoder.JSONDecodeError as ex:
                    ex.add_note(path)
                    raise ex

    @staticmethod
    def write(obj, path=""):
        "write object to disk."
        with lock:
            if path == "":
                path = Methods.ident(obj)
            pth = os.path.join(Workdir.wdr, "store", path)
            Util.cdir(pth)
            with open(pth, "w", encoding="utf-8") as fpt:
                Json.dump(obj, fpt, indent=4)
            Cache.sync(path, obj)
            return path


"locate"


class Locate:

    @staticmethod
    def attrs(kind):
        "show attributes for kind of objects."
        pth, obj = Locate.find(kind, nritems=1)
        if obj:
            return list(Dict.keys(obj))
        return []

    @staticmethod
    def find(kind, selector={}, removed=False, matching=False, nritems=None):
        "locate objects by matching atributes."
        nrs = 0
        res = []
        for pth in Locate.fns(Workdir.long(kind)):
            obj = Cache.get(pth)
            if not obj:
                obj = Object()
                Disk.read(obj, pth)
                Cache.add(pth, obj)
            if not removed and Methods.deleted(obj):
                continue
            if selector and not Methods.search(obj, selector, matching):
                continue
            if nritems and nrs >= nritems:
                break
            nrs += 1
            res.append((pth, obj))
        return res

    @staticmethod
    def fns(kind):
        "file names by kind of object."
        path = os.path.join(Workdir.wdr, "store", kind)
        for rootdir, dirs, _files in os.walk(path, topdown=True):
            for dname in dirs:
                if dname.count("-") != 2:
                    continue
                ddd = os.path.join(rootdir, dname)
                for fll in os.listdir(ddd):
                    yield Util.strip(os.path.join(ddd, fll))

    @staticmethod
    def last(obj, selector={}):
        "last saved version."
        result = sorted(
                        Locate.find(Methods.fqn(obj), selector),
                        key=lambda x: Time.fntime(x[0])
                       )
        res = ""
        if result:
            inp = result[-1]
            Dict.update(obj, inp[-1])
            res = inp[0]
        return res


"utilities"


class Util:

    @staticmethod
    def cdir(path):
        "create directory."
        pth = pathlib.Path(path)
        pth.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def strip(path):
        "strip filename from path."
        return path.split('store')[-1][1:]


"interface"


def __dir__():
    return (
        'Cache',
        'Disk',
        'Locate',
        'Util',
        'Workdir'
    )
