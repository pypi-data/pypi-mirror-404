# This file is placed in the Public Domain.


import os


d = os.path.dirname


def pth(event):
    path = d(d(__file__))
    path = os.path.join(path, "nucleus", "index.html")
    event.reply(f"file://{path}")
