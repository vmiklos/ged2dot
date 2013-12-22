#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import traceback

import ged2dot

import unohelper
from com.sun.star.beans import XPropertyAccess
from com.sun.star.ui.dialogs import XExecutableDialog
from com.sun.star.document import XImporter
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL as ExecutableDialogResults_CANCEL
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK as ExecutableDialogResults_OK
from com.sun.star.awt.PushButtonType import OK as PushButtonType_OK
from com.sun.star.awt.PushButtonType import CANCEL as PushButtonType_CANCEL
from com.sun.star.beans import PropertyValue


class GedcomDialog(unohelper.Base, XPropertyAccess, XExecutableDialog, XImporter):
    def __init__(self, context):
        self.context = context

    def __createUnoService(self, name):
        return self.context.ServiceManager.createInstanceWithContext(name, self.context)

    def __toDict(self, args):
        ret = {}
        for i in args:
            ret[i.Name] = i.Value
        return ret

    def __toTuple(self, args):
        ret = []
        for k, v in args.items():
            value = PropertyValue()
            value.Name = k
            value.Value = v
            ret.append(value)
        return tuple(ret)

    def __extractFamilies(self):
        ged = unohelper.fileUrlToSystemPath(self.props['URL'])
        configDict = {
            'ged2dot': {
                'input': ged,
                # We want a simple list of families, just give something.
                'rootFamily': 'F1'
            }
        }
        config = ged2dot.Config(configDict)
        model = ged2dot.Model(config)
        model.load(config.input)
        self.familyDict = {}
        for i in model.families:
            help = ""
            if i.husb and i.husb.surname:
                help += i.husb.surname
            help += "-"
            if i.wife and i.wife.surname:
                help += i.wife.surname
            key = "%s (%s)" % (i.id, help)
            self.familyDict[key] = i

    def __createControl(self, xParent, type, id, tabIndex, left, top, width, height,
                        value=None, buttonType=None):
        control = xParent.createInstance(type)
        control.PositionX = left
        control.PositionY = top
        control.Width = width
        control.Height = height
        control.Name = id
        control.TabIndex = tabIndex
        if type == "com.sun.star.awt.UnoControlFixedTextModel":
            control.Label = value
        elif type == "com.sun.star.awt.UnoControlButtonModel":
            control.PushButtonType = buttonType
            control.DefaultButton = buttonType == PushButtonType_OK
        elif type == "com.sun.star.awt.UnoControlListBoxModel":
            control.Dropdown = True
            # TODO check if we could make item text and data independent
            control.StringItemList = tuple(sorted(self.familyDict.keys(), key=lambda i: int(i.split(' (')[0][1:])))
            # Select the first item.
            control.SelectedItems = tuple([0])
        xParent.insertByName(id, control)
        return control

    def __execDialog(self):
        # .ui files can't be used in extensions ATM, so just to have some guidelines, here are the basics:
        # 1) Control width: 50, 100, etc -- based on demand.
        # 2) Control height, padding: 10
        # The rest is just derived from this.

        # Create the dialog model.
        xDialogModel = self.__createUnoService("com.sun.star.awt.UnoControlDialogModel")
        xDialogModel.PositionX = 0
        xDialogModel.PositionY = 0
        xDialogModel.Width = 230
        xDialogModel.Height = 50
        xDialogModel.Title = "GEDCOM Import"

        # Then the model of the controls.
        ftRootFamily = self.__createControl(xDialogModel, type="com.sun.star.awt.UnoControlFixedTextModel",
                                            id="ftRootFamily", tabIndex=0, left=10, top=10, width=100, height=10, value="Root family")
        cbRootFamily = self.__createControl(xDialogModel, type="com.sun.star.awt.UnoControlListBoxModel",
                                            id="cbRootFamily", tabIndex=1, left=120, top=10, width=100, height=10)
        btnOk = self.__createControl(xDialogModel, type="com.sun.star.awt.UnoControlButtonModel",
                                     id="btnOk", tabIndex=2, left=110, top=30, width=50, height=10, buttonType=PushButtonType_OK)
        btnCancel = self.__createControl(xDialogModel, type="com.sun.star.awt.UnoControlButtonModel",
                                         id="btnCancel", tabIndex=3, left=170, top=30, width=50, height=10, buttonType=PushButtonType_CANCEL)

        # Finally show the dialog.
        xDialog = self.__createUnoService("com.sun.star.awt.UnoControlDialog")
        xDialog.setModel(xDialogModel)
        xToolkit = self.__createUnoService("com.sun.star.awt.ExtToolkit")
        xDialog.createPeer(xToolkit, None)
        ret = xDialog.execute()
        if ret == ExecutableDialogResults_OK:
            key = cbRootFamily.StringItemList[cbRootFamily.SelectedItems[0]]
            self.rootFamily = self.familyDict[key].id
        return ret

    # XPropertyAccess
    def getPropertyValues(self):
        try:
            return self.__toTuple(self.props)
        except:
            traceback.print_exc(file=sys.stderr)

    def setPropertyValues(self, props):
        try:
            self.props = self.__toDict(props)
        except:
            traceback.print_exc(file=sys.stderr)

    # XExecutableDialog
    def setTitle(self, title):
        pass

    def execute(self):
        try:
            self.__extractFamilies()
            ret = self.__execDialog()
            if ret == ExecutableDialogResults_OK:
                self.props['FilterData'] = self.__toTuple({'rootFamily': self.rootFamily})
            return ret
        except:
            traceback.print_exc(file=sys.stderr)
            return ExecutableDialogResults_CANCEL

    # XImporter
    def setTargetDocument(self, xDstDoc):
        self.xDstDoc = xDstDoc

# vim:set shiftwidth=4 softtabstop=4 expandtab:
