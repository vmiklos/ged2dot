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
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Tuple

import uno  # type: ignore
import unohelper  # type: ignore
from com.sun.star.document import XFilter  # type: ignore
from com.sun.star.document import XImporter
from com.sun.star.document import XExtendedFilterDetection
from com.sun.star.beans import PropertyValue  # type: ignore

import ged2dot
import inlineize
import base


class GedcomImport(unohelper.Base, XFilter, XImporter, XExtendedFilterDetection, base.GedcomBase):  # type: ignore
    type = "draw_GEDCOM"

    def __init__(self, context: Any) -> None:
        unohelper.Base.__init__(self)
        base.GedcomBase.__init__(self, context)
        self.props = {}  # type: Dict[str, Any]
        self.dst_doc = None

    def __to_svg(self, ged: str) -> bytes:
        root_family = "F1"
        layout_max_depth = "4"
        name_order = "little"
        if "FilterData" in self.props.keys():
            filter_data = self.to_dict(self.props["FilterData"])
            if "rootfamily" in filter_data.keys():
                root_family = filter_data["rootfamily"]
            if "familydepth" in filter_data.keys():
                layout_max_depth = filter_data["familydepth"]
            if "nameorder" in filter_data.keys():
                name_order = filter_data["nameorder"]
        dot = io.StringIO()
        config = {
            'input': ged,
            'rootfamily': root_family,
            'familydepth': layout_max_depth,
            'nameorder': name_order,
            "imagedir": "images",
        }

        # Now do the actual ged2dot conversion.
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        for node in graph:
            node.resolve(graph)
        root_node = ged2dot.graph_find(graph, config["rootfamily"])
        assert root_node
        subgraph = ged2dot.bfs(root_node, config)
        exporter = ged2dot.DotExport()
        exporter.store_to_stream(subgraph, dot, config)

        if sys.platform.startswith("win"):
            pattern = os.environ['PROGRAMFILES'] + '\\Graphviz*\\bin\\dot.exe'
            dot_paths = glob.glob(pattern)
            if not dot_paths and 'PROGRAMFILES(x86)' in os.environ.keys():
                pattern = os.environ['PROGRAMFILES(x86)'] + '\\Graphviz*\\bin\\dot.exe'
                dot_paths = glob.glob(pattern)
            if not dot_paths:
                url = "<https://graphviz.gitlab.io/_pages/Download/Download_windows.html>"
                raise Exception("No dot.exe found at '%s', please download it from %s." % (pattern, url))
            dot_path = dot_paths[-1]
        else:
            dot_path = "dot"
        graphviz = subprocess.Popen([dot_path, '-Tsvg'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        dot.seek(0)
        assert graphviz.stdin
        graphviz.stdin.write(dot.read().encode('utf-8'))
        graphviz.stdin.close()
        noinline = io.BytesIO()
        assert graphviz.stdout
        noinline.write(graphviz.stdout.read())
        graphviz.stdout.close()
        graphviz.wait()

        noinline.seek(0)
        inline = io.BytesIO()
        inlineize.inlineize(noinline, inline)

        inline.seek(0)
        return inline.read()

    @staticmethod
    def __detect(input_stream: Any) -> bool:
        byte_sequence = uno.ByteSequence(bytes())
        # Input with and without UTF-8 BOM is OK.
        for i in ["0 HEAD", "\ufeff0 HEAD"]:
            input_stream.seek(0)
            # readBytes() returns a (read, byte_sequence) tuple.
            byte_sequence = input_stream.readBytes(byte_sequence, len(i.encode('utf-8')))[1]
            if byte_sequence.value.decode('utf-8') == i:
                return True
        return False

    # XFilter
    def filter(self, props: Dict[str, Any]) -> bool:
        try:
            self.props = self.to_dict(props)
            path = unohelper.fileUrlToSystemPath(self.props["URL"])
            buf = self.__to_svg(path)
            input_stream = self.create_uno_service("io.SequenceInputStream")
            input_stream.initialize((uno.ByteSequence(buf),))

            svg_filter = self.create_uno_service("comp.Draw.SVGFilter")
            svg_filter.setTargetDocument(self.dst_doc)

            value = PropertyValue()
            value.Name = "InputStream"
            value.Value = input_stream
            svg_filter.filter((value,))
            return True
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()
            return False

    # XImporter
    # pylint: disable=invalid-name
    def setTargetDocument(self, dst_doc: Any) -> None:
        try:
            self.dst_doc = dst_doc
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()

    # XExtendedFilterDetection
    def detect(self, args: Iterable[Any]) -> Tuple[str, Iterable[Any]]:
        try:
            dictionary = self.to_dict(args)
            if self.__detect(dictionary["InputStream"]):
                dictionary["TypeName"] = GedcomImport.type
                return GedcomImport.type, self.to_tuple(dictionary)
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()
        return "", args

# vim:set shiftwidth=4 softtabstop=4 expandtab:
