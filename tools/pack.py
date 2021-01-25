#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""Wrapper around pyinstaller."""

import subprocess
import sys


def main() -> None:
    """Commandline interface to this module."""
    args = ["pyinstaller", "-y", "--clean", "--windowed"]

    if sys.platform == "darwin":
        args.extend(["--icon", "icon.icns"])
        args.extend(["--osx-bundle-identifier", "hu.vmiklos.ged2dot"])

    for sex in ["f", "m", "u"]:
        args.append("--add-data=placeholder-" + sex + ".png:.")
    args.append("qged2dot.py")
    subprocess.run(args, check=True)


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
