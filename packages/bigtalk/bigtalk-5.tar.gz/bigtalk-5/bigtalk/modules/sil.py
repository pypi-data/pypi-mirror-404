# This file is placed in the Public Domain.


from bigtalk.brokers import Broker


def sil(event):
    bot = Broker.get(event.orig)
    bot.silent = True
    event.reply("ok")


def lou(event):
    bot = Broker.get(event.orig)
    bot.silent = False
    event.reply("ok")
