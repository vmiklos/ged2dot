#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
sys.path.append(sys.path[0]+"/..")
import ged2dot
import unittest
import os

class Test(unittest.TestCase):
    def convert(self, name):
        config = ged2dot.Config("%src" % name)
        model = ged2dot.Model(config)
        model.load(config.input)
        try:
            os.unlink("%s.dot" % name)
        except OSError:
            pass
        sock = open("%s.dot" % name, "w")
        saved = sys.stdout
        sys.stdout = sock
        model.save()
        sys.stdout = saved
        sock.close()

    def test_hello(self):
        self.convert('hello')

    def test_noyeardate(self):
        self.convert('noyeardate')

if __name__ == '__main__':
    unittest.main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
