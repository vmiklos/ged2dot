#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""Wrapper around pyinstaller."""

import os
import platform
import shutil
import subprocess
import sys
import zipfile
import glob

from msicreator import createmsi


def run_pyinstaller() -> None:
    """Invokes pyinstaller with the platform-specific flags."""
    args = ["pyinstaller", "-y", "--clean", "--windowed"]

    if sys.platform == "darwin":
        args.extend(["--icon", "icon.icns"])
        args.extend(["--osx-bundle-identifier", "hu.vmiklos.ged2dot"])
    elif sys.platform.startswith("win"):
        args.extend(["--icon", "icon.ico"])

    args.append("--additional-hooks-dir=pyi")
    for sex in ["f", "m", "u"]:
        args.append("--add-data=placeholder-" + sex + ".svg" + os.pathsep + ".")
    args.append("--add-data=marriage.svg" + os.pathsep + ".")
    args.append("--add-data=icon.svg" + os.pathsep + ".")
    args.append("qged2dot.py")
    print("Running '" + " ".join(args) + "'...")
    subprocess.run(args, check=True)


def get_version() -> str:
    """Extracts the version number from the Makefile."""
    version = ""
    with open("Makefile", encoding="utf-8") as stream:
        for line in stream.readlines():
            if line.startswith("VERSION = "):
                version = line.split(" = ")[1].strip()
                break

    system = platform.system().lower()
    version += "-" + system
    machine = platform.machine().lower()
    if sys.platform.startswith("win") and machine == "amd64":
        machine = "x64"
    version += "-" + machine
    return version


def main() -> None:
    """Commandline interface to this module."""
    run_pyinstaller()
    version = get_version()
    if sys.platform == "darwin":
        args = ["hdiutil", "create", "dist/qged2dot-" + version + ".dmg", "-srcfolder", "dist/qged2dot.app", "-ov"]
        # hdiutil sometimes fails with "create failed - Resource busy"
        # when that happens, we run it again
        for _ in range(2):
            try:
                print("Running '" + " ".join(args) + "'...")
                subprocess.run(args, check=True)
            except subprocess.CalledProcessError:
                continue
            break
        return
    if sys.platform.startswith("win"):
        os.chdir("dist")
        shutil.copyfile("../msi/LICENSE.rtf", "LICENSE.rtf")
        with open("../msi/qged2dot.json", "r", encoding="utf-8") as stream:
            buf = stream.read()
        with open("qged2dot.json", "w", encoding="utf-8") as stream:
            stream.write(buf.replace("1.0.0", version.split("-")[0]))
        print("Running createmsi...")
        createmsi.run(["qged2dot.json"])
        old_path = glob.glob("*.msi")[0]
        new_path = "qged2dot-" + version + ".msi"
        os.rename(old_path, new_path)
        print("Created '" + new_path + "'.")
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
