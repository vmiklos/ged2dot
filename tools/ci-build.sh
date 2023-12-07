#!/bin/bash -ex
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

#
# Baseline: Ubuntu 20.04 and macOS 10.15.
#

if [ "$GITHUB_JOB" == "macos" ]; then
    # See <https://github.com/actions/setup-python/issues/577>.
    rm /usr/local/bin/2to3-3.*
    rm /usr/local/bin/idle3.*
    rm /usr/local/bin/pydoc3.*
    rm /usr/local/bin/python3.*
    rm /usr/local/bin/2to3
    rm /usr/local/bin/idle3
    rm /usr/local/bin/pydoc3
    rm /usr/local/bin/python3-config

    brew install graphviz
elif [ -n "$GITHUB_JOB" ]; then
    sudo apt-get install graphviz graphviz-dev
fi

cd tools
git clone https://github.com/jpakkane/msicreator
cd msicreator
# Allow to add extra attributes to MajorUpgrade node. (#7), 2018-09-08.
git checkout 57c0d083ee8ce6d5c9b417d88aa80a1c8d3d6419
cd ..
cd ..

pip install -r requirements.txt

make -j$(getconf _NPROCESSORS_ONLN) check

make pack

# vim:set shiftwidth=4 softtabstop=4 expandtab:
