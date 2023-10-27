#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""Fuzzer for the GEDCOM parser."""

import atheris  # type: ignore

with atheris.instrument_imports():
    import ged2dot
    import io
    import sys
    import unittest.mock


class BufferHolder:
    """Mock for sys.stdin."""
    def __init__(self) -> None:
        self.buffer = io.BytesIO()


def test_one_input(data: bytes) -> None:
    """Tests one particular input."""
    stdin = BufferHolder()
    stdin.buffer.write(data)
    stdin.buffer.seek(0)
    with unittest.mock.patch('sys.stdin', stdin):
        try:
            ged2dot.main()
        except ged2dot.Ged2DotException:
            pass


atheris.Setup(sys.argv, test_one_input)
atheris.Fuzz()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
