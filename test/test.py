#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
import unittest
import ged2dot


class Test(unittest.TestCase):
    def convert(self, name, configDict={}):  # type: ignore
        if len(configDict):
            config = ged2dot.Config(configDict)  # type: ignore
        else:
            config = ged2dot.Config(["%src" % name])  # type: ignore
        model = ged2dot.Model(config)
        model.load(config.input)
        try:
            os.unlink("%s.dot" % name)
        except OSError:
            pass
        sock = open("%s.dot" % name, "w")
        model.save(sock)
        sock.close()
        return model

    def test_hello(self):  # type: ignore
        configDict = {
            'ged2dot': {
                'input': 'hello.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('hello', configDict)

    def test_partialname(self):  # type: ignore
        configDict = {
            'ged2dot': {
                'input': 'partial-name.ged',
                'rootFamily': 'F1'
            }
        }
        model = self.convert('partial-name', configDict)
        indi = model.getIndividual("P48")
        assert("None" not in indi.getLabel())

    def test_husbcousin(self):  # type: ignore
        # Layout failed when handling cousins on the left edge of the layout.
        configDict = {
            'ged2dot': {
                'input': 'husb-cousin.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('bom', configDict)

    def test_bom(self):  # type: ignore
        # Parser failed as the input file had a leading BOM.
        configDict = {
            'ged2dot': {
                'input': 'bom.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('bom', configDict)

    def test_noyeardate(self):  # type: ignore
        configDict = {
            'ged2dot': {
                'input': 'noyeardate.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('noyeardate', configDict)

    def test_nohusb(self):  # type: ignore
        # This tests if placeholder nodes are created for missing husbands.
        configDict = {
            'ged2dot': {
                'input': 'nohusb.ged',
                'rootFamily': 'F3'
            }
        }
        self.convert('nohusb', configDict)

    def test_nowife(self):  # type: ignore
        # This tests if placeholder nodes are created for missing wifes.
        configDict = {
            'ged2dot': {
                'input': 'nowife.ged',
                'rootFamily': 'F3'
            }
        }
        self.convert('nowife', configDict)

    def test_screenshot(self):  # type: ignore
        # This is the demo input from the README, make sure it works.
        # Also, this time use a config file path, to test that as well.
        self.convert('screenshot')

    def test_descendants(self):  # type: ignore
        self.convert('descendants')


if __name__ == '__main__':
    unittest.main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
