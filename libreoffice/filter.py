#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import io
import subprocess
import sys
import traceback

import uno
import unohelper
from com.sun.star.document import XFilter
from com.sun.star.document import XImporter
from com.sun.star.document import XExtendedFilterDetection
from com.sun.star.beans import PropertyValue

import ged2dot
import inlineize


class GedcomImport(unohelper.Base, XFilter, XImporter, XExtendedFilterDetection):
    type = "draw_GEDCOM"

    def __init__(self, context):
        self.context = context

    # TODO create base class for these 3 methods
    def __createUnoService(self, name):
        return self.context.ServiceManager.createInstanceWithContext(name, self.context)

    def __toDict(self, args):
        ret = {}
        for i in args:
            ret[i.Name] = i.Value
        return ret

    def __toTuple(self, args):
        ret = []
        for k, v in args.items():
            value = PropertyValue()
            value.Name = k
            value.Value = v
            ret.append(value)
        return tuple(ret)

    def __toSvg(self, ged):
        rootFamily = ged2dot.Config.rootFamilyDefault
        layoutMaxDepth = ged2dot.Config.layoutMaxDepthDefault
        if "FilterData" in self.props.keys():
            filterData = self.__toDict(self.props["FilterData"])
            if "rootFamily" in filterData.keys():
                rootFamily = filterData["rootFamily"]
            if "layoutMaxDepth" in filterData.keys():
                layoutMaxDepth = filterData["layoutMaxDepth"]
        configDict = {
            'ged2dot': {
                'input': ged,
                'rootFamily': rootFamily,
                'layoutMaxDepth': layoutMaxDepth
            }
        }
        config = ged2dot.Config(configDict)
        model = ged2dot.Model(config)
        model.load(config.input)
        dot = io.StringIO()
        model.save(dot)

        graphviz = subprocess.Popen(['dot', '-Tsvg'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
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
        bytes = uno.ByteSequence('')
        magic = "0 HEAD"
        read, bytes = xInputStream.readBytes(bytes, len(magic))
        return bytes.value.decode('utf-8') == magic

    # XFilter
    def filter(self, props):
        try:
            self.props = self.__toDict(props)
            path = unohelper.fileUrlToSystemPath(self.props["URL"])
            buf = self.__toSvg(path)
            xInputStream = self.__createUnoService("com.sun.star.io.SequenceInputStream")
            xInputStream.initialize((uno.ByteSequence(buf),))

            xFilter = self.__createUnoService("com.sun.star.comp.Draw.SVGFilter")
            xFilter.setTargetDocument(self.xDstDoc)

            value = PropertyValue()
            value.Name = "InputStream"
            value.Value = xInputStream
            xFilter.filter((value,))
            return True
        except:
            traceback.print_exc(file=sys.stderr)
            return False

    # XImporter
    def setTargetDocument(self, xDstDoc):
        self.xDstDoc = xDstDoc

    # XExtendedFilterDetection
    def detect(self, args):
        try:
            dict = self.__toDict(args)
            if self.__detect(dict["InputStream"]):
                dict["TypeName"] = GedcomImport.type
                return GedcomImport.type, self.__toTuple(dict)
        except:
            traceback.print_exc(file=sys.stderr)
        return ""

# vim:set shiftwidth=4 softtabstop=4 expandtab:
