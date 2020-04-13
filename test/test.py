#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import io
import os
import sys
import unittest
import unittest.mock
from typing import Any
from typing import List
from typing import cast
import ged2dot


def mock_sys_exit(ret: List[int]) -> Any:
    """Mocks sys.exit()."""
    def mock(code: int) -> None:
        ret.append(code)
    return mock


class Test(unittest.TestCase):
    @staticmethod
    def convert(name: str, config_dict: Any) -> ged2dot.Model:
        if config_dict:
            config = ged2dot.Config(config_dict)
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
        config_dict = {
            'ged2dot': {
                'input': 'hello.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('hello', config_dict)

    def test_partialname(self) -> None:
        config_dict = {
            'ged2dot': {
                'input': 'partial-name.ged',
                'rootFamily': 'F1'
            }
        }
        model = self.convert('partial-name', config_dict)
        indi = model.get_individual("P48")
        assert indi
        self.assertTrue("None" not in indi.get_label())

    def test_nosex(self) -> None:
        # Capture standard output.
        buf = io.StringIO()
        with unittest.mock.patch('sys.stderr', buf):
            ret = []  # type: List[int]
            with unittest.mock.patch('sys.exit', mock_sys_exit(ret)):
                # if there is no sex, this should fail and indicate line number
                config_dict = {
                    'ged2dot': {
                        'input': 'nosex.ged',
                        'rootFamily': 'F1'
                    }
                }
                self.convert('nosex', config_dict)
                self.assertEqual(ret, [1])
                buf.seek(0)
                expected = "Encountered parsing error in .ged: list index out of range\n"
                expected += "line (12): 1 SEX\n"
                self.assertEqual(buf.read(), expected)

    def test_husbcousin(self) -> None:
        # Layout failed when handling cousins on the left edge of the layout.
        config_dict = {
            'ged2dot': {
                'input': 'husb-cousin.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('bom', config_dict)

    def test_bom(self) -> None:
        # Parser failed as the input file had a leading BOM.
        config_dict = {
            'ged2dot': {
                'input': 'bom.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('bom', config_dict)

    def test_noyeardate(self) -> None:
        config_dict = {
            'ged2dot': {
                'input': 'noyeardate.ged',
                'rootFamily': 'F1'
            }
        }
        self.convert('noyeardate', config_dict)

    def test_nohusb(self) -> None:
        # This tests if placeholder nodes are created for missing husbands.
        config_dict = {
            'ged2dot': {
                'input': 'nohusb.ged',
                'rootFamily': 'F3'
            }
        }
        self.convert('nohusb', config_dict)

    def test_nowife(self) -> None:
        # This tests if placeholder nodes are created for missing wifes.
        config_dict = {
            'ged2dot': {
                'input': 'nowife.ged',
                'rootFamily': 'F3'
            }
        }
        self.convert('nowife', config_dict)

    def test_screenshot(self) -> None:
        # This is the demo input from the README, make sure it works.
        # Also, this time use a config file path, to test that as well.
        self.convert('screenshot', {})

    def test_descendants(self) -> None:
        self.convert('descendants', {})

    def test_layout_max_sibling_depth(self) -> None:
        """
        Test that in case siblings are hidden in all ancestor generations, then P9 (Greg) doesn't
        show up in the output. Without the explicit layoutMaxSiblingDepth=0, layoutMaxDepth=1 would
        pull that in.
        """
        config_dict = {
            'ged2dot': {
                'input': 'layout-max-sibling-depth.ged',
                'rootFamily': 'F1',
                'layoutMaxDepth': 1,
                'layoutMaxSiblingDepth': 0
            }
        }
        config = ged2dot.Config(config_dict)
        model = ged2dot.Model(config)
        model.load(config.input)
        layout = ged2dot.Layout(model, sys.stdout)
        layout.calc()
        for subgraph in layout.subgraphs:
            for element in subgraph.elements:
                if element.__class__ == ged2dot.Node:
                    node = cast(ged2dot.Node, element)
                    self.assertTrue(node.node_id != "p9")


if __name__ == '__main__':
    unittest.main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
