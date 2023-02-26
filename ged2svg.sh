#!/bin/bash -ex
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

#
# This script runs ged2dot, dot and inlineize to create an inline SVG.
#

GED2DOT=$(dirname $(realpath $0))/ged2dot.py
$GED2DOT --config ged2dotrc

dot -Tsvg -o test.svg test.dot

INLINEIZE=$(dirname $(realpath $0))/inlineize.py
$INLINEIZE test.svg test-inline.svg

# vim:set shiftwidth=4 softtabstop=4 expandtab:
