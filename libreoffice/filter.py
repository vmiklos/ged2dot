#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import glob
import io
import os
import subprocess
import sys

import uno
import unohelper
from com.sun.star.document import XFilter
from com.sun.star.document import XImporter
from com.sun.star.document import XExtendedFilterDetection
from com.sun.star.beans import PropertyValue

import ged2dot
import inlineize
import base


class GedcomImport(unohelper.Base, XFilter, XImporter, XExtendedFilterDetection, base.GedcomBase):
    type = "draw_GEDCOM"

    def __init__(self, context):
        base.GedcomBase.__init__(self, context)

    def __toSvg(self, ged):
        rootFamily = ged2dot.Config.rootFamilyDefault
        layoutMaxDepth = ged2dot.Config.layoutMaxDepthDefault
        nodeLabelImage = ged2dot.Config.nodeLabelImageDefault
        if "FilterData" in self.props.keys():
            filterData = self.toDict(self.props["FilterData"])
            if "rootFamily" in filterData.keys():
                rootFamily = filterData["rootFamily"]
            if "layoutMaxDepth" in filterData.keys():
                layoutMaxDepth = filterData["layoutMaxDepth"]
            if "nodeLabelImage" in filterData.keys():
                nodeLabelImage = filterData["nodeLabelImage"]
        configDict = {
            'ged2dot': {
                'input': ged,
                'rootFamily': rootFamily,
                'layoutMaxDepth': layoutMaxDepth,
                'nodeLabelImage': nodeLabelImage
            }
        }
        config = ged2dot.Config(configDict)
        model = ged2dot.Model(config)
        model.load(config.input)
        dot = io.StringIO()
        model.save(dot)

        if sys.platform.startswith("win"):
            pattern = os.environ['PROGRAMFILES'] + '\\Graphviz*\\bin\\dot.exe'
            dotPaths = glob.glob(pattern)
            if not len(dotPaths):
                raise Exception("No dot.exe found at '%s', please download it from <http://www.graphviz.org/Download_windows.php>." % pattern)
            dotPath = dotPaths[-1]
        else:
            dotPath = "dot"
        graphviz = subprocess.Popen([dotPath, '-Tsvg'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        dot.seek(0)
        graphviz.stdin.write(dot.read().encode('utf-8'))
        graphviz.stdin.close()
        noinline = io.BytesIO()
        noinline.write(graphviz.stdout.read())
        graphviz.stdout.close()
        graphviz.wait()

        noinline.seek(0)
        inline = io.BytesIO()
        inlineize.inlineize(noinline, inline)

        inline.seek(0)
        return inline.read()

    def __detect(self, xInputStream):
        byteSequence = uno.ByteSequence(bytes())
        # Input with and without UTF-8 BOM is OK.
        for i in ["0 HEAD", "\ufeff0 HEAD"]:
            xInputStream.seek(0)
            # readBytes() returns a (read, byteSequence) tuple.
            byteSequence = xInputStream.readBytes(byteSequence, len(i.encode('utf-8')))[1]
            if byteSequence.value.decode('utf-8') == i:
                return True
        return False

    # XFilter
    def filter(self, props):
        try:
            self.props = self.toDict(props)
            path = unohelper.fileUrlToSystemPath(self.props["URL"])
            buf = self.__toSvg(path)
            xInputStream = self.createUnoService("io.SequenceInputStream")
            xInputStream.initialize((uno.ByteSequence(buf),))

            xFilter = self.createUnoService("comp.Draw.SVGFilter")
            xFilter.setTargetDocument(self.xDstDoc)

            value = PropertyValue()
            value.Name = "InputStream"
            value.Value = xInputStream
            xFilter.filter((value,))
            return True
        except Exception:
            self.printTraceback()
            return False

    # XImporter
    def setTargetDocument(self, xDstDoc):
        self.xDstDoc = xDstDoc

    # XExtendedFilterDetection
    def detect(self, args):
        try:
            dict = self.toDict(args)
            if self.__detect(dict["InputStream"]):
                dict["TypeName"] = GedcomImport.type
                return GedcomImport.type, self.toTuple(dict)
        except Exception:
            self.printTraceback()
        return ""

# vim:set shiftwidth=4 softtabstop=4 expandtab:
