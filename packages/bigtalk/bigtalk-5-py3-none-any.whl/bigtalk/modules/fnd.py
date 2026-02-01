# This file is placed in the Public Domain.


import time


from bigtalk.defines import Locate, Methods, Time, Workdir


def fnd(event):
    if not event.rest:
        res = sorted([x.split('.')[-1].lower() for x in Workdir.kinds()])
        if res:
            event.reply(",".join(res))
        else:
            event.reply("no data yet.")
        return
    otype = event.args[0]
    nmr = 0
    for fnm, obj in sorted(Locate.find(otype, event.gets), key=lambda x: Time.fntime(x[0])):
        event.reply(f"{nmr} {Methods.fmt(obj)} {Time.elapsed(time.time()-Time.fntime(fnm))}")
        nmr += 1
    if not nmr:
        event.reply("no result")
