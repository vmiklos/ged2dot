#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
import sys
import traceback
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Tuple
import uno  # type: ignore  # Cannot find module named 'uno'
from com.sun.star.beans import PropertyValue  # type: ignore  # Cannot find module named 'com.sun.star.beans'


class GedcomBase:
    def __init__(self, context: Any) -> None:
        self.context = context

    def create_uno_service(self, name: str) -> Any:
        return self.context.ServiceManager.createInstanceWithContext("com.sun.star.%s" % name, self.context)

    @staticmethod
    def to_dict(args: Iterable[Any]) -> Dict[str, Any]:
        ret = {}
        for i in args:
            ret[i.Name] = i.Value
        return ret

    @staticmethod
    def to_tuple(args: Dict[str, Any]) -> Tuple[Any, ...]:
        ret = []
        for key, value in args.items():
            value = PropertyValue()
            value.Name = key
            value.Value = value
            ret.append(value)
        return tuple(ret)

    def print_traceback(self) -> None:
        if sys.platform.startswith("win"):
            path_substitution = self.context.ServiceManager.createInstance("com.sun.star.util.PathSubstitution")
            user = path_substitution.getSubstituteVariableValue("user")
            path = uno.fileUrlToSystemPath(user + "/Scripts/python/log.txt")
            directory = os.path.dirname(path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            sock = open(path, "a")
            traceback.print_exc(file=sock)
            sock.close()
        else:
            traceback.print_exc(file=sys.stderr)

# vim:set shiftwidth=4 softtabstop=4 expandtab:
