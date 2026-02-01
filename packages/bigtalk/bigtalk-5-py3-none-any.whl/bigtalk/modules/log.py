# This file is placed in the Public Domain.


import time


from bigtalk.defines import Disk, Locate, Object, Time


class Log(Object):

    def __init__(self):
        super().__init__()
        self.txt = ''


def log(event):
    if not event.rest:
        nmr = 0
        for fnm, obj in Locate.find('log', event.gets):
            lap = Time.elapsed(time.time() - Time.fntime(fnm))
            event.reply(f'{nmr} {obj.txt} {lap}')
            nmr += 1
        if not nmr:
            event.reply('no log')
        return
    obj = Log()
    obj.txt = event.rest
    Disk.write(obj)
    event.reply("ok")
