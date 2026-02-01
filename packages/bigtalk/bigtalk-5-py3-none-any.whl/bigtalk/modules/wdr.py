# This file is placed in the Public Domain.


"working directory"


from bigtalk.persist import Workdir


def wdr(event):
    event.reply(Workdir.workdir())
