#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""Turns linked graphics into inline graphics in an SVG file."""

import base64
import mimetypes
import sys
from typing import IO
from typing import Union
from xml.etree import ElementTree

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'


def get_mimetype(href: str) -> str:
    """Returns the MIME type of the given path."""
    mimetype = mimetypes.guess_type(href)[0]
    if mimetype is None:
        return 'application/octet-stream'
    return mimetype


def inlineize(from_path: Union[str, IO[bytes]], to_path: Union[str, IO[bytes]]) -> None:
    """API interface to this module."""
    ElementTree.register_namespace('', SVG_NS)
    ElementTree.register_namespace('xlink', XLINK_NS)
    tree = ElementTree.ElementTree()
    tree.parse(from_path)
    svg_ns = "{" + SVG_NS + "}"
    xlink_ns = "{" + XLINK_NS + "}"
    for image in tree.findall(f".//{svg_ns}image"):
        xlinkhref = f"{xlink_ns}href"
        href = image.attrib[xlinkhref]
        with open(href, 'rb') as stream:
            b64 = base64.b64encode(stream.read()).decode('ascii')
            image.attrib[xlinkhref] = f"data:{get_mimetype(href)};base64,{b64}"
    tree.write(to_path)


def main() -> None:
    """Commandline interface to this module."""
    inlineize(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
