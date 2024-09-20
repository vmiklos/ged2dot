#!/bin/bash -ex
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

sudo apt-get update
sudo apt-get install graphviz graphviz-dev
# for pylint and pyqt6
sudo apt-get install xorg libxkbcommon0

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
