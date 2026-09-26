#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0

"""The test_inlineize module covers the inlineize module."""

import os
import tempfile
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
            self.assertNotIn("xlink:href=\"data:image/jpeg;base64,", buffer)
            self.assertNotIn("xlink:href=\"data:image/svg+xml;base64,", buffer)
        argv = ["", "tests/linked.svg", "tests/inline.svg"]
        with unittest.mock.patch('sys.argv', argv):
            inlineize.main()
        with open("tests/inline.svg", "r", encoding="utf-8") as stream:
            buffer = stream.read()
            self.assertNotIn("xlink:href\"tests/images", buffer)
            self.assertIn("xlink:href=\"data:image/jpeg;base64,", buffer)
            self.assertIn("xlink:href=\"data:image/svg+xml;base64,", buffer)

    def test_unknown_extension(self) -> None:
        """Tests that an image with an unknown extension gets a fallback MIME type."""
        with tempfile.TemporaryDirectory(prefix="inlineize") as tmpdir:
            linked = os.path.join(tmpdir, "linked.svg")
            inline = os.path.join(tmpdir, "inline.svg")
            image = os.path.join(tmpdir, "image.qqu")
            with open(linked, "w", encoding="utf-8") as stream:
                stream.write(
                    f'<svg xmlns="{inlineize.SVG_NS}" '
                    f'xmlns:xlink="{inlineize.XLINK_NS}">'
                    f'<image xlink:href="{image}"/></svg>'
                )
            with open(image, "wb") as stream:
                stream.write(b"data")
            inlineize.inlineize(linked, inline)
            with open(inline, "r", encoding="utf-8") as stream:
                buffer = stream.read()
                self.assertIn("xlink:href=\"data:application/octet-stream;base64,", buffer)


if __name__ == '__main__':
    unittest.main()
