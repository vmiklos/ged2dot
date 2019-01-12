#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import ged2dot
import base

import unohelper
from com.sun.star.beans import XPropertyAccess
from com.sun.star.ui.dialogs import XExecutableDialog
from com.sun.star.document import XImporter
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL as ExecutableDialogResults_CANCEL
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK as ExecutableDialogResults_OK
from com.sun.star.awt.PushButtonType import OK as PushButtonType_OK
from com.sun.star.awt.PushButtonType import CANCEL as PushButtonType_CANCEL


class GedcomDialog(unohelper.Base, XPropertyAccess, XExecutableDialog, XImporter, base.GedcomBase):
    def __init__(self, context, dialogArgs):
        base.GedcomBase.__init__(self, context)

    def __extractFamilies(self):
        ged = unohelper.fileUrlToSystemPath(self.props['URL'])
        configDict = {
            'ged2dot': {
                'input': ged,
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
        control = xParent.createInstance("com.sun.star.awt.UnoControl%sModel" % type)
        control.PositionX = left
        control.PositionY = top
        control.Width = width
        control.Height = height
        control.Name = id
        control.TabIndex = tabIndex
        if type == "FixedText":
            control.Label = value
        elif type == "Button":
            control.PushButtonType = buttonType
            control.DefaultButton = buttonType == PushButtonType_OK
        elif type == "ListBox":
            control.Dropdown = True
            # TODO check if we could make item text and data independent
            control.StringItemList = tuple(sorted(self.familyDict.keys(), key=lambda i: int(i.split(' (')[0][1:])))
            # Select the first item.
            control.SelectedItems = tuple([0])
        elif type == "NumericField":
            control.Spin = True
            control.Value = ged2dot.Config.layoutMaxDepthDefault
            control.DecimalAccuracy = 0
            control.ValueMin = 0
        elif type == "CheckBox":
            control.Label = value
            control.State = 1
        xParent.insertByName(id, control)
        return control

    def __execDialog(self):
        # .ui files can't be used in extensions ATM, so just to have some guidelines, here are the basics:
        # 1) Control width: 50, 100, etc -- based on demand.
        # 2) Control height, padding: 10
        # The rest is just derived from this.

        # Create the dialog model.
        xDialogModel = self.createUnoService("awt.UnoControlDialogModel")
        xDialogModel.PositionX = 0
        xDialogModel.PositionY = 0
        xDialogModel.Width = 230
        xDialogModel.Height = 90
        xDialogModel.Title = "GEDCOM Import"

        # Then the model of the controls.
        self.__createControl(xDialogModel, type="FixedText", id="ftRootFamily", tabIndex=0, left=10, top=10, width=100, height=10, value="Root family")
        lbRootFamily = self.__createControl(xDialogModel, type="ListBox", id="lbRootFamily", tabIndex=1, left=120, top=10, width=100, height=10)
        self.__createControl(xDialogModel, type="FixedText", id="ftLayoutMax", tabIndex=2, left=10, top=30, width=100, height=10, value="Number of generations to show")
        nfLayoutMax = self.__createControl(xDialogModel, type="NumericField", id="nfLayoutMax", tabIndex=3, left=120, top=30, width=100, height=10)
        self.__createControl(xDialogModel, type="FixedText", id="ftNameOrder", tabIndex=4, left=10, top=50, width=100, height=10, value="Name order")
        cbNameOrder = self.__createControl(xDialogModel, type="CheckBox", id="cbNameOrder", tabIndex=5, left=120, top=50, width=100, height=10, value="Forename first")
        self.__createControl(xDialogModel, type="Button", id="btnOk", tabIndex=6, left=110, top=70, width=50, height=10, buttonType=PushButtonType_OK)
        self.__createControl(xDialogModel, type="Button", id="btnCancel", tabIndex=7, left=170, top=70, width=50, height=10, buttonType=PushButtonType_CANCEL)

        # Finally show the dialog.
        xDialog = self.createUnoService("awt.UnoControlDialog")
        xDialog.setModel(xDialogModel)
        xToolkit = self.createUnoService("awt.ExtToolkit")
        xDialog.createPeer(xToolkit, None)
        ret = xDialog.execute()
        if ret == ExecutableDialogResults_OK:
            key = lbRootFamily.StringItemList[lbRootFamily.SelectedItems[0]]
            self.rootFamily = self.familyDict[key].id
            self.layoutMax = int(nfLayoutMax.Value)
            if cbNameOrder.State:
                self.nodeLabelImage = ged2dot.Config.nodeLabelImageDefault
            else:
                self.nodeLabelImage = ged2dot.Config.nodeLabelImageSwappedDefault
        return ret

    # XPropertyAccess
    def getPropertyValues(self):
        try:
            return self.toTuple(self.props)
        except Exception:
            self.printTraceback()

    def setPropertyValues(self, props):
        try:
            self.props = self.toDict(props)
        except Exception:
            self.printTraceback()

    # XExecutableDialog
    def setTitle(self, title):
        pass

    def execute(self):
        try:
            self.__extractFamilies()
            ret = self.__execDialog()
            if ret == ExecutableDialogResults_OK:
                self.props['FilterData'] = self.toTuple({
                    'rootFamily': self.rootFamily,
                    'layoutMaxDepth': self.layoutMax,
                    'nodeLabelImage': self.nodeLabelImage
                })
            return ret
        except Exception:
            self.printTraceback()
            return ExecutableDialogResults_CANCEL

    # XImporter
    def setTargetDocument(self, xDstDoc):
        self.xDstDoc = xDstDoc

# vim:set shiftwidth=4 softtabstop=4 expandtab:
