#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import io
import os
import unittest
import unittest.mock
from typing import Any
from typing import List
import ged2dot


def mock_sys_exit(ret: List[int]) -> Any:
    """Mocks sys.exit()."""
    def mock(code: int) -> None:
        ret.append(code)
    return mock


class Test(unittest.TestCase):
    @staticmethod
    def convert(name: str, configDict: Any) -> ged2dot.Model:
        if configDict:
            config = ged2dot.Config(configDict)
        else:
            config = ged2dot.Config(["%src" % name])
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

    def test_hello(self) -> None:
        configDict = {
            'ged2dot': {
                'input': 'hello.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('hello', configDict)

    def test_partialname(self) -> None:
        configDict = {
            'ged2dot': {
                'input': 'partial-name.ged',
                'rootFamily': 'F1'
            }
        }
        model = self.convert('partial-name', configDict)
        indi = model.getIndividual("P48")
        assert indi
        self.assertTrue("None" not in indi.getLabel())

    def test_nosex(self) -> None:
        # Capture standard output.
        buf = io.StringIO()
        with unittest.mock.patch('sys.stdout', buf):
            ret = []  # type: List[int]
            with unittest.mock.patch('sys.exit', mock_sys_exit(ret)):
                # if there is no sex, this should fail and indicate line number
                configDict = {
                    'ged2dot': {
                        'input': 'nosex.ged',
                        'rootFamily': 'F1'
                    }
                }
                self.convert('nosex', configDict)
                self.assertEqual(ret, [1])
                buf.seek(0)
                expected = "Encountered parsing error in .ged: list index out of range\n"
                expected += "line (12): 1 SEX\n"
                self.assertEqual(buf.read(), expected)

    def test_husbcousin(self) -> None:
        # Layout failed when handling cousins on the left edge of the layout.
        configDict = {
            'ged2dot': {
                'input': 'husb-cousin.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('bom', configDict)

    def test_bom(self) -> None:
        # Parser failed as the input file had a leading BOM.
        configDict = {
            'ged2dot': {
                'input': 'bom.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('bom', configDict)

    def test_noyeardate(self) -> None:
        configDict = {
            'ged2dot': {
                'input': 'noyeardate.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('noyeardate', configDict)

    def test_nohusb(self) -> None:
        # This tests if placeholder nodes are created for missing husbands.
        configDict = {
            'ged2dot': {
                'input': 'nohusb.ged',
                'rootFamily': 'F3'
            }
        }
        self.convert('nohusb', configDict)

    def test_nowife(self) -> None:
        # This tests if placeholder nodes are created for missing wifes.
        configDict = {
            'ged2dot': {
                'input': 'nowife.ged',
                'rootFamily': 'F3'
            }
        }
        self.convert('nowife', configDict)

    def test_screenshot(self) -> None:
        # This is the demo input from the README, make sure it works.
        # Also, this time use a config file path, to test that as well.
        self.convert('screenshot', {})

    def test_descendants(self) -> None:
        self.convert('descendants', {})


if __name__ == '__main__':
    unittest.main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
