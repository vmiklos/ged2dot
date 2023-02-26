#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""Wrapper around 'pip list --outdated'."""

import subprocess


def main() -> None:
    """Commandline interface to this module."""
    requirements = []
    with open("requirements.txt", encoding="utf-8") as sock:
        for line in sock.readlines():
            requirements.append(line.split("==")[0])
    requirements = sorted(set(requirements))

    completed_process = subprocess.run(["pip", "list", "--outdated"], capture_output=True, check=True)
    lineno = 0
    lines = completed_process.stdout.decode("utf-8")
    for line in lines.split("\n"):
        lineno += 1
        if not line:
            continue

        if lineno <= 2 or line.split(" ")[0] in requirements:
            print(line)


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
