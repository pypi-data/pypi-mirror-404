# This file is placed in the Public Domain.


"a clean namespace"


import json
import types


class Reserved(Exception):

    pass


"object"


class Object:

    def __contains__(self, key):
        return key in dir(self)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class Dict:

    @staticmethod
    def clear(obj):
        "remove all items from the object."
        obj.__dict__.clear()


    @staticmethod
    def construct(obj, *args, **kwargs):
        "object contructor."
        if args:
            val = args[0]
            if isinstance(val, zip):
                Dict.update(obj, dict(val))
            elif isinstance(val, dict):
                Dict.update(obj, val)
            else:
                Dict.update(obj, vars(val))
        if kwargs:
            Dict.update(obj, kwargs)

    @staticmethod
    def copy(obj):
        "return shallow copy of the object."
        oobj = type(obj)()
        Dict.update(oobj, obj.__dict__.copy())
        return oobj

    @staticmethod
    def fromkeys(obj, keyz, value=None):
        "create a new object with keys from iterable and values set to value/"
        return obj.__dict__.fromkeys(keyz, value)

    @staticmethod
    def get(obj, key, default=None):
        "return value for key if key is in the object, otherwise return default."
        return obj.__dict__.get(key, default)

    @staticmethod
    def items(obj):
        "object's key,value pairs."
        if isinstance(obj, dict):
            return obj.items()
        if isinstance(obj, types.MappingProxyType):
            return obj.items()
        return obj.__dict__.items()

    @staticmethod
    def keys(obj):
        "object's keys."
        if isinstance(obj, dict):
            return obj.keys()
        if isinstance(obj, types.MappingProxyType):
            return obj.keys()
        return obj.__dict__.keys()

    @staticmethod
    def pop(obj, key, default=None):
        "remove key from object and return it's value. return default or KeyError."
        return obj.__dict__.pop(key, default)

    @staticmethod
    def popitem(obj):
        "remove and return (key, value) pair."
        return obj.__dict__.popitem()

    @staticmethod
    def update(obj, data, empty=True):
        "update object,"
        if isinstance(obj, dict):
            obj.update(data)
        elif isinstance(obj.__dict__, types.MappingProxyType):
            for key, value in data.items():
                setattr(obj, key, value)
        elif isinstance(data, dict):
            obj.__dict__.update(data)
        else:
            obj.__dict__.update(data.__dict__)

    @staticmethod
    def values(obj):
        "object's values."
        if isinstance(obj, dict):
            return obj.values()
        elif isinstance(obj.__dict__, types.MappingProxyType):
            res = []
            for key in obj.__dict__:
                res.append(obj[key])
            return res
        return obj.__dict__.values()


"default"


class Default(Object):

    def __getattr__(self, key):
        return self.__dict__.get(key, "")


"json"


class Encoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, dict):
            return o.items()
        if isinstance(o, list):
            return iter(o)
        if isinstance(o, types.MappingProxyType):
            return dict(o)
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            try:
                return vars(o)
            except TypeError:
                return repr(o)

class Json:

    @staticmethod
    def dump(*args, **kw):
        "dump object to disk."
        kw["cls"] = Encoder
        return json.dump(*args, **kw)

    @staticmethod
    def dumps(*args, **kw):
        "dump object to string."
        kw["cls"] = Encoder
        return json.dumps(*args, **kw)

    @staticmethod
    def load(s, *args, **kw):
        "load object from disk."
        return json.load(s, *args, **kw)

    @staticmethod
    def loads(s, *args, **kw):
        "load object from string."
        return json.loads(s, *args, **kw)


"interface"


def __dir__():
    return (
        'Default',
        'Dict',
        'Json',
        'Object'
    )
