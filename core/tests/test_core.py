#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""The test_core module covers the core module."""

import os
import unittest

import core


class TestMain(unittest.TestCase):
    """Tests main()."""
    def test_happy(self) -> None:
        """Tests the happy path."""
        config = {
            "familyDepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootFamily": "F1",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        core.convert(config)
        self.assertTrue(os.path.exists(config["output"]))

    def test_bom(self) -> None:
        """Tests handling of an UTF-8 BOM."""
        config = {
            "familyDepth": "4",
            "input": "tests/bom.ged",
            "output": "tests/bom.dot",
            "rootFamily": "F1",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        # Without the accompanying fix in place, this test would have failed with:
        # ValueError: invalid literal for int() with base 10: '\ufeff0'
        core.convert(config)
        self.assertTrue(os.path.exists(config["output"]))


if __name__ == '__main__':
    unittest.main()
