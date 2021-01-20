#!/bin/bash -ex
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

#
# Baseline: Ubuntu 20.04 and macOS 10.15.
#

pip install -r requirements.txt

make -j$(getconf _NPROCESSORS_ONLN) check

make pack

# vim:set shiftwidth=4 softtabstop=4 expandtab:
