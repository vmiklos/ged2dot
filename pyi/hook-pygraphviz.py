#!/usr/bin/env python3

"""Pygraphviz hook for pyinstaller."""

import glob
import os
import shutil

from PyInstaller.compat import is_win, is_darwin
from PyInstaller.depend.bindepend import findLibrary

binaries = []
datas = []

# List of binaries agraph.py may invoke.
progs = [
    "neato",
    "dot",
    "twopi",
    "circo",
    "fdp",
    "nop",
    "acyclic",
    "gvpr",
    "gvcolor",
    "ccomps",
    "sccmap",
    "tred",
    "sfdp",
    "unflatten",
]

if is_win:
    for prog in progs:
        for binary in glob.glob("c:/Program Files/Graphviz*/bin/" + prog + ".exe"):
            binaries.append((binary, "."))
    for binary in glob.glob("c:/Program Files/Graphviz*/bin/*.dll"):
        binaries.append((binary, "."))
    for data in glob.glob("c:/Program Files/Graphviz*/bin/config*"):
        datas.append((data, "."))
else:
    # The dot binary in PATH is typically a symlink, handle that.
    # graphviz_bindir is e.g. /usr/local/Cellar/graphviz/2.46.0/bin
    graphviz_bindir = os.path.dirname(os.path.realpath(shutil.which("dot")))
    for binary in progs:
        binaries.append((graphviz_bindir + "/" + binary, "."))
    if is_darwin:
        suffix = "dylib"
        # graphviz_libdir is e.g. /usr/local/Cellar/graphviz/2.46.0/lib/graphviz
        graphviz_libdir = os.path.realpath(graphviz_bindir + "/../lib/graphviz")
    else:
        suffix = "so"
        # graphviz_libdir is e.g. /usr/lib64/graphviz
        graphviz_libdir = os.path.join(os.path.dirname(findLibrary('libcdt')), 'graphviz')
    for binary in glob.glob(graphviz_libdir + "/*." + suffix):
        binaries.append((binary, "graphviz"))
    for data in glob.glob(graphviz_libdir + "/config*"):
        datas.append((data, "graphviz"))


# vim:set shiftwidth=4 softtabstop=4 expandtab:
