#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

from typing import Any
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Tuple

import unohelper  # type: ignore  # Cannot find module named 'unohelper'
from com.sun.star.beans import XPropertyAccess  # type: ignore  # Cannot find module named 'com.sun.star.beans'
from com.sun.star.ui.dialogs import XExecutableDialog  # type: ignore  # Cannot find module named 'com.sun.star.ui.dialogs'
from com.sun.star.document import XImporter  # type: ignore  # Cannot find module named 'com.sun.star.document'
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL as ExecutableDialogResults_CANCEL  # type: ignore  # Cannot find module named 'com.sun.star.ui.dialogs.ExecutableDialogResults'
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK as ExecutableDialogResults_OK
from com.sun.star.awt.PushButtonType import OK as PushButtonType_OK  # type: ignore  # Cannot find module named 'com.sun.star.awt.PushButtonType'
from com.sun.star.awt.PushButtonType import CANCEL as PushButtonType_CANCEL

import ged2dot
import base


class GedcomDialog(unohelper.Base, XPropertyAccess, XExecutableDialog, XImporter, base.GedcomBase):  # type: ignore  # Class cannot subclass
    def __init__(self, context: Any, _dialogArgs: Any) -> None:
        unohelper.Base.__init__(self)
        base.GedcomBase.__init__(self, context)

    def __extractFamilies(self) -> None:
        ged = unohelper.fileUrlToSystemPath(self.props['URL'])
        configDict = {
            'ged2dot': {
                'input': ged,
            }
        }
        config = ged2dot.Config(configDict)
        model = ged2dot.Model(config)
        model.load(config.input)
        self.familyDict = {}  # type: Dict[str, ged2dot.Family]
        for i in model.families:
            help_string = ""
            if i.husb and i.husb.surname:
                help_string += i.husb.surname
            help_string += "-"
            if i.wife and i.wife.surname:
                help_string += i.wife.surname
            key = "%s (%s)" % (i.id, help_string)
            self.familyDict[key] = i

    def __createControl(self, xParent: Any, type_string: str, id_string: str, tabIndex: int, left: int, top: int, width: int, height: int,
                        value: Optional[str] = None, buttonType: Optional[int] = None) -> Any:
        control = xParent.createInstance("com.sun.star.awt.UnoControl%sModel" % type_string)
        control.PositionX = left
        control.PositionY = top
        control.Width = width
        control.Height = height
        control.Name = id_string
        control.TabIndex = tabIndex
        if type_string == "FixedText":
            control.Label = value
        elif type_string == "Button":
            control.PushButtonType = buttonType
            control.DefaultButton = buttonType == PushButtonType_OK
        elif type_string == "ListBox":
            control.Dropdown = True
            # TODO check if we could make item text and data independent
            control.StringItemList = tuple(sorted(self.familyDict.keys(), key=lambda i: int(i.split(' (')[0][1:])))
            # Select the first item.
            control.SelectedItems = tuple([0])
        elif type_string == "NumericField":
            control.Spin = True
            control.Value = ged2dot.Config.layoutMaxDepthDefault
            control.DecimalAccuracy = 0
            control.ValueMin = 0
        elif type_string == "CheckBox":
            control.Label = value
            control.State = 1
        xParent.insertByName(id_string, control)
        return control

    def __execDialog(self) -> Any:
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
        self.__createControl(xDialogModel, type_string="FixedText", id_string="ftRootFamily", tabIndex=0, left=10, top=10, width=100, height=10, value="Root family")
        lbRootFamily = self.__createControl(xDialogModel, type_string="ListBox", id_string="lbRootFamily", tabIndex=1, left=120, top=10, width=100, height=10)
        self.__createControl(xDialogModel, type_string="FixedText", id_string="ftLayoutMax", tabIndex=2, left=10, top=30, width=100, height=10, value="Number of generations to show")
        nfLayoutMax = self.__createControl(xDialogModel, type_string="NumericField", id_string="nfLayoutMax", tabIndex=3, left=120, top=30, width=100, height=10)
        self.__createControl(xDialogModel, type_string="FixedText", id_string="ftNameOrder", tabIndex=4, left=10, top=50, width=100, height=10, value="Name order")
        cbNameOrder = self.__createControl(xDialogModel, type_string="CheckBox", id_string="cbNameOrder", tabIndex=5, left=120, top=50, width=100, height=10, value="Forename first")
        self.__createControl(xDialogModel, type_string="Button", id_string="btnOk", tabIndex=6, left=110, top=70, width=50, height=10, buttonType=PushButtonType_OK)
        self.__createControl(xDialogModel, type_string="Button", id_string="btnCancel", tabIndex=7, left=170, top=70, width=50, height=10, buttonType=PushButtonType_CANCEL)

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
    def getPropertyValues(self) -> Tuple[Any, ...]:
        try:
            return self.toTuple(self.props)
        # pylint: disable=broad-except
        except Exception:
            self.printTraceback()

        return ()

    def setPropertyValues(self, props: Iterable[Any]) -> None:
        try:
            self.props = self.toDict(props)
        # pylint: disable=broad-except
        except Exception:
            self.printTraceback()

    # XExecutableDialog
    def setTitle(self, title: str) -> None:
        pass

    def execute(self) -> Any:
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
        # pylint: disable=broad-except
        except Exception:
            self.printTraceback()
            return ExecutableDialogResults_CANCEL

    # XImporter
    def setTargetDocument(self, xDstDoc: Any) -> None:
        self.xDstDoc = xDstDoc

# vim:set shiftwidth=4 softtabstop=4 expandtab:
