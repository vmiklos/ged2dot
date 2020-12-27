#!/bin/bash -ex
#
# Copyright 2020 Miklos Vajna. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#

#
# This script runs all the tests for CI purposes.
#

pip install -r requirements.txt
make -j$(getconf _NPROCESSORS_ONLN) check

cd core
pip install -r requirements.txt
make -j$(getconf _NPROCESSORS_ONLN) check

# vim:set shiftwidth=4 softtabstop=4 expandtab:
