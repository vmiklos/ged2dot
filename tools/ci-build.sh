#!/bin/bash -ex
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

#
# Baseline: Ubuntu 20.04 and macOS 10.15.
#

if [ "$GITHUB_JOB" == "macos" ]; then
    brew install graphviz
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
