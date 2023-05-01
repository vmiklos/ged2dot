#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

#
# Baseline: Windows 2019
#
Set-PSDebug -Trace 1

choco install graphviz --version 2.48.0
if (-not $?) { throw "error $?" }
# Register plugins.
dot -c
if (-not $?) { throw "error $?" }
choco install wixtoolset
if (-not $?) { throw "error $?" }

cd tools
git clone https://github.com/jpakkane/msicreator
if (-not $?) { throw "error $?" }
cd msicreator
# Allow to add extra attributes to MajorUpgrade node. (#7), 2018-09-08.
git checkout 57c0d083ee8ce6d5c9b417d88aa80a1c8d3d6419
if (-not $?) { throw "error $?" }
cd ..
cd ..

# Allow both 'graphviz' and 'Graphviz <version>'.
$GVPATH = Resolve-Path "C:/Program Files/Graphviz*" | Select -ExpandProperty Path
python -m pip install --config-settings="--global-option=build_ext" --config-settings="--global-option=-I${GVPATH}/include" --config-settings="--global-option=-L${GVPATH}/lib/" pygraphviz==1.10
if (-not $?) { throw "error $?" }
python -m pip install -r requirements.txt
if (-not $?) { throw "error $?" }

python tools\pack.py
if (-not $?) { throw "error $?" }

# vim:set shiftwidth=4 softtabstop=4 expandtab:
