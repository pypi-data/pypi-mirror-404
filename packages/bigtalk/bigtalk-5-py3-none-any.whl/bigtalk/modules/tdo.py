# This file is placed in the Public Domain.


import time


from bigtalk.defines import Disk, Locate, Object, Time


class Todo(Object):

    def __init__(self):
        Object.__init__(self)
        self.txt = ''


def dne(event):
    if not event.args:
        event.reply("dne <txt>")
        return
    selector = {'txt': event.args[0]}
    nmr = 0
    for fnm, obj in Locate.find('todo', selector):
        nmr += 1
        obj.__deleted__ = True
        Disk.write(obj, fnm)
        event.reply("ok")
        break
    if not nmr:
        event.reply("nothing todo")


def tdo(event):
    if not event.rest:
        nmr = 0
        for fnm, obj in Locate.find('todo', event.gets):
            lap = Time.elapsed(time.time()-Time.fntime(fnm))
            event.reply(f'{nmr} {obj.txt} {lap}')
            nmr += 1
        if not nmr:
            event.reply("no todo")
        return
    obj = Todo()
    obj.txt = event.rest
    Disk.write(obj)
    event.reply("ok")
