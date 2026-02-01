# This file is placed in the Public Domain.


"an object as the first argument"


import datetime
import os


from .objects import Default, Dict


"methods"


class Methods:

    @staticmethod
    def deleted(obj):
        "check whether obj had deleted flag set."
        return "__deleted__" in dir(obj) and obj.__deleted__

    @staticmethod
    def edit(obj, setter={}, skip=False):
        "update object with dict."
        for key, val in Dict.items(setter):
            if skip and val == "":
                continue
            Methods.typed(obj, key, val)

    @staticmethod
    def fmt(obj, args=[], skip=[], plain=False, empty=False):
        "format object info printable string."
        if args == []:
            args = list(obj.__dict__.keys())
        txt = ""
        for key in args:
            if key.startswith("__"):
                continue
            if key in skip:
                continue
            value = getattr(obj, key, None)
            if value is None:
                continue
            if not empty and not value:
                continue
            if plain:
                txt += f"{value} "
            elif isinstance(value, (int, float, dict, bool, list)):
                txt += f"{key}={value} "
            elif isinstance(value, str):
                txt += f'{key}="{value}" '
            else:
                txt += f"{key}={Methods.fqn(value)}((value))"
        if txt == "":
            txt = "{}"
        return txt.strip()

    @staticmethod
    def fqn(obj):
        "full qualified name."
        kin = str(type(obj)).split()[-1][1:-2]
        if kin == "type":
            kin = f"{obj.__module__}.{obj.__name__}"
        return kin

    @staticmethod
    def ident(obj):
        "return ident string for object."
        return os.path.join(Methods.fqn(obj), *str(datetime.datetime.now()).split())

    @staticmethod
    def parse(obj, text):
        "parse text for command."
        data = {
            "args": [],
            "cmd": "",
            "gets": Default(),
            "index": None,
            "init": "",
            "opts": "",
            "otxt": text,
            "rest": "",
            "silent": Default(),
            "sets": Default(),
            "text": text
        }
        for k, v in data.items():
            setattr(obj, k, getattr(obj, k, v) or v)
        args = []
        nr = -1
        for spli in text.split():
            if spli.startswith("-"):
                try:
                    obj.index = int(spli[1:])
                except ValueError:
                    obj.opts += spli[1:]
                continue
            if "-=" in spli:
                key, value = spli.split("-=", maxsplit=1)
                Methods.typed(obj.silent, key, value)
                Methods.typed(obj.gets, key, value)
                continue
            if "==" in spli:
                key, value = spli.split("==", maxsplit=1)
                Methods.typed(obj.gets, key, value)
                continue
            if "=" in spli:
                key, value = spli.split("=", maxsplit=1)
                Methods.typed(obj.sets, key, value)
                continue
            nr += 1
            if nr == 0:
                obj.cmd = spli
                continue
            args.append(spli)
        if args:
            obj.args = args
            obj.text  = obj.cmd or ""
            obj.rest = " ".join(obj.args)
            obj.text  = obj.cmd + " " + obj.rest
        else:
            obj.text = obj.cmd or ""

    @staticmethod
    def search(obj, selector={}, matching=False):
        "check whether object matches search criteria."
        res = False
        for key, value in Dict.items(selector):
            val = getattr(obj, key, None)
            if not val:
                res = False
                break
            if matching and value != val:
               res = False
               break
            if str(value).lower() not in str(val).lower():
               res = False
               break
            res = True
        return res

    @staticmethod
    def skip(obj, chars="_"):
        "skip keys containing chars."
        res = {}
        for key, value in Dict.items(obj):
            next = False
            for char in chars:
                if char in key:
                    next = True
            if next:
                continue
            res[key] = value
        return res

    @staticmethod
    def typed(obj, key, val):
        "assign proper types."
        try:
            setattr(obj, key, int(val))
            return
        except ValueError:
            pass
        try:
            setattr(obj, key, float(val))
            return
        except ValueError:
           pass
        if val in ["True", "true", True]:
            setattr(obj, key, True)
        elif val in ["False", "false", False]:
            setattr(obj, key, False)
        else:
            setattr(obj, key, val)


"interface"


def __dir__():
    return (
        'Methods',
    )
