#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

from com.sun.star.beans import PropertyValue


class GedcomBase(object):
    def __init__(self, context):
        self.context = context

    def createUnoService(self, name):
        return self.context.ServiceManager.createInstanceWithContext(name, self.context)

    def toDict(self, args):
        ret = {}
        for i in args:
            ret[i.Name] = i.Value
        return ret

    def toTuple(self, args):
        ret = []
        for k, v in args.items():
            value = PropertyValue()
            value.Name = k
            value.Value = v
            ret.append(value)
        return tuple(ret)

# vim:set shiftwidth=4 softtabstop=4 expandtab:
