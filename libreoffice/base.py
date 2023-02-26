#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""The base module provides the GedcomBase class."""

import os
import sys
import traceback
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Tuple
import uno  # type: ignore  # pylint: disable=import-error
from com.sun.star.beans import PropertyValue  # type: ignore  # pylint: disable=import-error


class GedcomBase:
    """Shared code between GedcomDialog and GedcomImport."""
    def __init__(self, context: Any) -> None:
        self.context = context

    def create_uno_service(self, name: str) -> Any:
        """Creates an UNO object instalce with the given name."""
        return self.context.ServiceManager.createInstanceWithContext(f"com.sun.star.{name}", self.context)

    @staticmethod
    def to_dict(args: Iterable[Any]) -> Dict[str, Any]:
        """Turns a tuple of name-value pairs into a dict."""
        ret = {}
        for i in args:
            ret[i.Name] = i.Value
        return ret

    @staticmethod
    def to_tuple(args: Dict[str, Any]) -> Tuple[Any, ...]:
        """Turns a dict into a tuple of name-value pairs."""
        ret = []
        for arg_key, arg_value in args.items():
            value = PropertyValue()
            value.Name = arg_key
            value.Value = arg_value
            ret.append(value)
        return tuple(ret)

    def print_traceback(self) -> None:
        """Prints the backtrace on error."""
        if sys.platform.startswith("win"):
            path_substitution = self.context.ServiceManager.createInstance("com.sun.star.util.PathSubstitution")
            user = path_substitution.getSubstituteVariableValue("user")
            path = uno.fileUrlToSystemPath(user + "/Scripts/python/log.txt")
            directory = os.path.dirname(path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(path, "a", encoding="utf-8") as stream:
                traceback.print_exc(file=stream)
        else:
            traceback.print_exc(file=sys.stderr)

# vim:set shiftwidth=4 softtabstop=4 expandtab:
