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


def test_one_input(data: bytes) -> None:
    """Tests one particular input."""
    importer = ged2dot.GedcomImport()
    try:
        importer.tokenize_from_stream(io.BytesIO(data))
    except ged2dot.Ged2DotException:
        pass


atheris.Setup(sys.argv, test_one_input)
atheris.Fuzz()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
