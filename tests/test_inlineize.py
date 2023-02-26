#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0

"""The test_inlineize module covers the inlineize module."""

import unittest
import unittest.mock

import inlineize


class TestMain(unittest.TestCase):
    """Tests main()."""
    def test_happy(self) -> None:
        """Tests the happy path."""
        with open("tests/linked.svg", "r", encoding="utf-8") as stream:
            buffer = stream.read()
            self.assertIn("xlink:href=\"tests/images", buffer)
            self.assertNotIn("xlink:href=\"data:image/png;base64,", buffer)
        argv = ["", "tests/linked.svg", "tests/inline.svg"]
        with unittest.mock.patch('sys.argv', argv):
            inlineize.main()
        with open("tests/inline.svg", "r", encoding="utf-8") as stream:
            buffer = stream.read()
            self.assertNotIn("xlink:href\"tests/images", buffer)
            self.assertIn("xlink:href=\"data:image/png;base64,", buffer)


if __name__ == '__main__':
    unittest.main()
