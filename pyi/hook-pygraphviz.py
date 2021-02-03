#!/usr/bin/env python3

"""Pygraphviz hook for pyinstaller."""

import glob

from PyInstaller.compat import is_win, is_darwin

binaries = []
datas = []

if is_darwin:
    for binary in glob.glob("/usr/local/Cellar/graphviz/*/bin/dot"):
        binaries.append((binary, "."))
    for binary in glob.glob("/usr/local/Cellar/graphviz/*/lib/graphviz/*.dylib"):
        binaries.append((binary, "graphviz"))
    for data in glob.glob("/usr/local/Cellar/graphviz/*/lib/graphviz/config*"):
        datas.append((data, "graphviz"))

if is_win:
    for binary in glob.glob("c:/Program Files/Graphviz*/bin/dot.exe"):
        binaries.append((binary, "."))
    for binary in glob.glob("c:/Program Files/Graphviz*/bin/*.dll"):
        binaries.append((binary, "."))
    for data in glob.glob("c:/Program Files/Graphviz*/bin/config*"):
        datas.append((data, "."))

# vim:set shiftwidth=4 softtabstop=4 expandtab:
