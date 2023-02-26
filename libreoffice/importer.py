#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""Provides the GedcomImport class."""

import glob
import io
import os
import subprocess
import sys
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Tuple

import uno  # type: ignore  # pylint: disable=import-error
import unohelper  # type: ignore  # pylint: disable=import-error
from com.sun.star.document import XFilter  # type: ignore  # pylint: disable=import-error
from com.sun.star.document import XImporter  # pylint: disable=import-error
from com.sun.star.document import XExtendedFilterDetection  # pylint: disable=import-error
from com.sun.star.beans import PropertyValue  # type: ignore  # pylint: disable=import-error

import base
import ged2dot
import inlineize


class GedcomImport(unohelper.Base, XFilter, XImporter, XExtendedFilterDetection, base.GedcomBase):  # type: ignore
    """Executes the import of the GEDCOM file after the options dialog."""
    type = "draw_GEDCOM"

    def __init__(self, context: Any) -> None:
        unohelper.Base.__init__(self)
        base.GedcomBase.__init__(self, context)
        self.props: Dict[str, Any] = {}
        self.dst_doc = None

    @staticmethod
    def __find_dot() -> str:
        if sys.platform.startswith("win"):
            pattern = os.environ['PROGRAMFILES'] + '\\Graphviz*\\bin\\dot.exe'
            dot_paths = glob.glob(pattern)
            if not dot_paths and 'PROGRAMFILES(x86)' in os.environ:
                pattern = os.environ['PROGRAMFILES(x86)'] + '\\Graphviz*\\bin\\dot.exe'
                dot_paths = glob.glob(pattern)
            if not dot_paths:
                url = "<https://graphviz.gitlab.io/_pages/Download/Download_windows.html>"
                raise IOError(f"No dot.exe found at '{pattern}', please download it from {url}.")
            dot_path = dot_paths[-1]
        else:
            dot_path = "dot"
        return dot_path

    @staticmethod
    def __to_dot(config: Dict[str, str]) -> io.BytesIO:
        dot = io.BytesIO()
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_node = ged2dot.graph_find(graph, config["rootfamily"])
        assert root_node
        subgraph = ged2dot.bfs(root_node, config)
        exporter = ged2dot.DotExport()
        exporter.store_to_stream(subgraph, dot, config)
        return dot

    def __to_svg(self, ged: str) -> bytes:
        root_family = "F1"
        layout_max_depth = "4"
        name_order = "little"
        if "FilterData" in self.props:
            filter_data = self.to_dict(self.props["FilterData"])
            root_family = filter_data.get("rootfamily", root_family)
            layout_max_depth = filter_data.get("familydepth", layout_max_depth)
            name_order = filter_data.get("nameorder", name_order)
        config = {
            'input': ged,
            'rootfamily': root_family,
            'familydepth': layout_max_depth,
            'nameorder': name_order,
            "imagedir": "images",
        }

        dot = self.__to_dot(config)

        dot_path = self.__find_dot()
        with subprocess.Popen([dot_path, '-Tsvg'], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as graphviz:
            dot.seek(0)
            assert graphviz.stdin
            graphviz.stdin.write(dot.read())
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

    def filter(self, props: Dict[str, Any]) -> bool:
        """XFilter, feeds out SVG output into the SVG importer."""
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

    def setTargetDocument(self, dst_doc: Any) -> None:  # pylint: disable=invalid-name
        """XImporter, sets the destination model."""
        try:
            self.dst_doc = dst_doc
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()

    def detect(self, args: Iterable[Any]) -> Tuple[str, Iterable[Any]]:
        """XExtendedFilterDetection, decides if the input is a GEDCOM file or not."""
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
