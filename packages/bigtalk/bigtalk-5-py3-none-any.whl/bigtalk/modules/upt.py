# This file is placed in the Public Domain.


import time


from bigtalk.defines import Time


STARTTIME = time.time()


def upt(event):
    event.reply(Time.elapsed(time.time()-STARTTIME))
