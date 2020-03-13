#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import base64
import sys
import xml.etree.ElementTree as ElementTree
from typing import Union
from typing import IO

NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'xlink': 'http://www.w3.org/1999/xlink'
}


def inlineize(from_path: Union[str, IO[bytes]], to_path: Union[str, IO[bytes]]) -> None:
    ElementTree.register_namespace('', NAMESPACES['svg'])
    ElementTree.register_namespace('xlink', NAMESPACES['xlink'])
    tree = ElementTree.ElementTree()
    tree.parse(from_path)
    for image in tree.findall('.//{%s}image' % NAMESPACES['svg']):
        xlinkhref = '{%s}href' % NAMESPACES['xlink']
        href = image.attrib[xlinkhref]
        sock = open(href, 'rb')
        image.attrib[xlinkhref] = "data:image/png;base64,%s" % base64.b64encode(sock.read()).decode('ascii')
        sock.close()
    tree.write(to_path)


def main() -> None:
    inlineize(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
