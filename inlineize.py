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

namespaces = {
    'svg': 'http://www.w3.org/2000/svg',
    'xlink': 'http://www.w3.org/1999/xlink'
}


def inlineize(fro: Union[str, IO[bytes]], to: Union[str, IO[bytes]]) -> None:
    ElementTree.register_namespace('', namespaces['svg'])
    ElementTree.register_namespace('xlink', namespaces['xlink'])
    tree = ElementTree.ElementTree()
    tree.parse(fro)
    for image in tree.findall('.//{%s}image' % namespaces['svg']):
        xlinkhref = '{%s}href' % namespaces['xlink']
        href = image.attrib[xlinkhref]
        sock = open(href, 'rb')
        image.attrib[xlinkhref] = "data:image/png;base64,%s" % base64.b64encode(sock.read()).decode('ascii')
        sock.close()
    tree.write(to)


def main() -> None:
    inlineize(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
