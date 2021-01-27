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
    elif sys.platform.startswith("win"):
        args.extend(["--icon", "icon.ico"])

    for sex in ["f", "m", "u"]:
        args.append("--add-data=placeholder-" + sex + ".png" + os.pathsep + ".")
    args.append("--add-data=icon.svg" + os.pathsep + ".")
    args.append("qged2dot.py")
    print("Running '" + " ".join(args) + "'...")
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
    version = get_version()
    system = platform.system().lower()
    if sys.platform == "darwin":
        system = "macos"
    version += "-" + system
    machine = platform.machine().lower()
    if system == "windows" and machine == "amd64":
        machine = "x64"
    version += "-" + machine
    if sys.platform == "darwin":
        args = ["hdiutil", "create", "dist/qged2dot-" + version + ".dmg", "-srcfolder", "dist/qged2dot.app", "-ov"]
        print("Running '" + " ".join(args) + "'...")
        subprocess.run(args, check=True)
        return

    os.chdir("dist")
    zip_path = "qged2dot-" + version + ".zip"
    print("Creating '" + zip_path + "'...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as stream:
        root_path = "qged2dot"
        for root, _dirs, files in os.walk(root_path):
            for file in files:
                stream.write(os.path.join(root, file),
                             os.path.relpath(os.path.join(root, file), os.path.join(root_path, '..')))


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
