# This file is placed in the Public Domain.


"module management"


import importlib.util
import logging
import os


from .command import Commands
from .objects import Default
from .threads import Thread
from .utility import Utils


"config"


class Config(Default):

    pass


Cfg = Config()



"mods"


class Mods:

    dirs = {}
    modules = {}

    @staticmethod
    def init(name, path):
        "add modules directory." 
        Mods.dirs[name] = path

    @staticmethod
    def get(modlist, ignore=""):
        "loop over modules."
        for pkgname, path in Mods.dirs.items():
            if not os.path.exists(path):
                continue
            for fnm in os.listdir(path):
                if fnm.startswith("__"):
                    continue
                if not fnm.endswith(".py"):
                    continue
                name = fnm[:-3]
                if name not in Utils.spl(modlist):
                    continue
                if ignore and name in Utils.spl(ignore):
                    continue
                modname = f"{pkgname}.{name}"
                mod =  Mods.modules.get(modname, None)
                if mod:
                    logging.debug(f"cache {mod}")
                else:
                    mod = Mods.importer(modname, os.path.join(path, fnm))
                    logging.debug(f"import {mod}")
                if mod:
                    yield name, mod

    @staticmethod
    def list(ignore=""):
        "comma seperated list of available modules."
        mods = []
        for pkgname, path in Mods.dirs.items():
            mods.extend([
                x[:-3] for x in os.listdir(path)
                if x.endswith(".py") and
                not x.startswith("__") and
                x[:-3] not in Utils.spl(ignore)
            ])
        return ",".join(sorted(mods))

    @staticmethod
    def importer(name, pth=""):
        "import module by path."
        if pth and os.path.exists(pth):
            spec = importlib.util.spec_from_file_location(name, pth)
        else:
            spec = importlib.util.find_spec(name)
        if not spec or not spec.loader:
            logging.debug(f"missing spec or loader for {name}")
            return None
        mod = importlib.util.module_from_spec(spec)
        if not mod:
            logging.debug(f"can't load {name} module from spec")
            return None
        Mods.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    @staticmethod
    def pkgname(obj):
        "package name of an object."
        return obj.__module__.split(".")[0]

    @staticmethod
    def inits(modlist, ignore="", wait=False):
        "scan named modules for commands."
        thrs = []
        for name, mod in Mods.get(modlist, ignore):
            if "init" in dir(mod):
                thrs.append((name, Thread.launch(mod.init)))
        if wait:
            for name, thr in thrs:
                thr.join()
        
    @staticmethod
    def scanner(modlist, ignore=""):
        "scan named modules for commands."
        res = []
        for name, mod in Mods.get(modlist, ignore):
            Commands.scan(mod)
            res.append((name, mod))
        return res


"interface"


def __dir__():
    return (
        'Mods',
    )
