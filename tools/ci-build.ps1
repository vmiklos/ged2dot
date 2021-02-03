#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

#
# Baseline: Windows 2019
#

choco install graphviz
# Register plugins.
dot -c
choco install wixtools

cd tools
git clone https://github.com/jpakkane/msicreator
cd msicreator
# Allow to add extra attributes to MajorUpgrade node. (#7), 2018-09-08.
git checkout 57c0d083ee8ce6d5c9b417d88aa80a1c8d3d6419
cd ..
cd ..

$GVPATH = Resolve-Path "C:/Program Files/Graphviz *" | Select -ExpandProperty Path
pip install --global-option=build_ext --global-option="-I${GVPATH}/include" --global-option="-L${GVPATH}/lib/" pygraphviz==1.6
python -m pip install -r requirements.txt

python tools\pack.py

# vim:set shiftwidth=4 softtabstop=4 expandtab:
