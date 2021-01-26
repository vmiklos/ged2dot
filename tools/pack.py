#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""Wrapper around pyinstaller."""

import subprocess
import sys
import os
import zipfile
import platform


def run_pyinstaller() -> None:
    """Invokes pyinstaller with the platform-specific flags."""
    args = ["pyinstaller", "-y", "--clean", "--windowed"]

    if sys.platform == "darwin":
        args.extend(["--icon", "icon.icns"])
        args.extend(["--osx-bundle-identifier", "hu.vmiklos.ged2dot"])

    for sex in ["f", "m", "u"]:
        args.append("--add-data=placeholder-" + sex + ".png" + os.pathsep + ".")
    args.append("qged2dot.py")
    subprocess.run(args, check=True)


def get_version() -> str:
    """Extracts the version number from the Makefile."""
    with open("Makefile") as stream:
        for line in stream.readlines():
            if line.startswith("VERSION = "):
                return line.split(" = ")[1].strip()
    return ""


def main() -> None:
    """Commandline interface to this module."""
    run_pyinstaller()
    if sys.platform == "darwin":
        # Using hdiutil instead.
        return

    version = get_version()
    version += "-" + platform.system().lower()
    version += "-" + platform.machine().lower()
    os.chdir("dist")
    with zipfile.ZipFile("qged2dot-" + version + ".zip", "w", zipfile.ZIP_DEFLATED) as stream:
        root_path = "qged2dot"
        for root, _dirs, files in os.walk(root_path):
            for file in files:
                stream.write(os.path.join(root, file),
                             os.path.relpath(os.path.join(root, file), os.path.join(root_path, '..')))


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
