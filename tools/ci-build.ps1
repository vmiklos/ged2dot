#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

Set-PSDebug -Trace 1

choco install graphviz --version 2.48.0
if (-not $?) { throw "error $?" }
# Register plugins.
dot -c
if (-not $?) { throw "error $?" }
dotnet tool install --global wix --version 4.0.5
if (-not $?) { throw "error $?" }
wix extension add -g WixToolset.UI.wixext/4.0.4
if (-not $?) { throw "error $?" }

cd tools
git clone https://github.com/jpakkane/msicreator
if (-not $?) { throw "error $?" }
cd msicreator
#  Custom actions (#15), 2024-03-13
git checkout 3942d6cbe41655b027f469c600b80ac021d05841
if (-not $?) { throw "error $?" }
cd ..
cd ..

# Allow both 'graphviz' and 'Graphviz <version>'.
$GVPATH = Resolve-Path "C:/Program Files/Graphviz*" | Select -ExpandProperty Path
python -m pip install --config-settings="--global-option=build_ext" --config-settings="--global-option=-I${GVPATH}/include" --config-settings="--global-option=-L${GVPATH}/lib/" pygraphviz==1.14
if (-not $?) { throw "error $?" }
python -m pip install -r requirements.txt
if (-not $?) { throw "error $?" }

python tools\pack.py
if (-not $?) { throw "error $?" }

# vim:set shiftwidth=4 softtabstop=4 expandtab:
