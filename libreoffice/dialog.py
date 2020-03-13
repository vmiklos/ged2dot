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
        self.family_dict = {}  # type: Dict[str, ged2dot.Family]
        self.root_family = None  # type: Optional[str]
        self.layout_max = 0
        self.node_label_image = ""
        self.props = {}  # type: Dict[str, Any]
        self.dst_doc = None

    def __extract_families(self) -> None:
        ged = unohelper.fileUrlToSystemPath(self.props['URL'])
        config_dict = {
            'ged2dot': {
                'input': ged,
            }
        }
        config = ged2dot.Config(config_dict)
        model = ged2dot.Model(config)
        model.load(config.input)
        self.family_dict = {}
        for i in model.families:
            help_string = ""
            if i.husb and i.husb.surname:
                help_string += i.husb.surname
            help_string += "-"
            if i.wife and i.wife.surname:
                help_string += i.wife.surname
            key = "%s (%s)" % (i.fid, help_string)
            self.family_dict[key] = i

    def __create_control(self, parent: Any, type_string: str, id_string: str, tab_index: int, left: int, top: int, width: int, height: int,
                         value: Optional[str] = None, button_type: Optional[int] = None) -> Any:
        control = parent.createInstance("com.sun.star.awt.UnoControl%sModel" % type_string)
        control.PositionX = left
        control.PositionY = top
        control.Width = width
        control.Height = height
        control.Name = id_string
        control.TabIndex = tab_index
        if type_string == "FixedText":
            control.Label = value
        elif type_string == "Button":
            control.PushButtonType = button_type
            control.DefaultButton = button_type == PushButtonType_OK
        elif type_string == "ListBox":
            control.Dropdown = True
            # TODO check if we could make item text and data independent
            control.StringItemList = tuple(sorted(self.family_dict.keys(), key=lambda i: int(i.split(' (')[0][1:])))
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
        parent.insertByName(id_string, control)
        return control

    def __exec_dialog(self) -> Any:
        # .ui files can't be used in extensions ATM, so just to have some guidelines, here are the basics:
        # 1) Control width: 50, 100, etc -- based on demand.
        # 2) Control height, padding: 10
        # The rest is just derived from this.

        # Create the dialog model.
        dialog_model = self.createUnoService("awt.UnoControlDialogModel")
        dialog_model.PositionX = 0
        dialog_model.PositionY = 0
        dialog_model.Width = 230
        dialog_model.Height = 90
        dialog_model.Title = "GEDCOM Import"

        # Then the model of the controls.
        self.__create_control(dialog_model, type_string="FixedText", id_string="ftRootFamily", tab_index=0, left=10, top=10, width=100, height=10, value="Root family")
        root_family_lb = self.__create_control(dialog_model, type_string="ListBox", id_string="root_family_lb", tab_index=1, left=120, top=10, width=100, height=10)
        self.__create_control(dialog_model, type_string="FixedText", id_string="ftLayoutMax", tab_index=2, left=10, top=30, width=100, height=10, value="Number of generations to show")
        layout_max_nf = self.__create_control(dialog_model, type_string="NumericField", id_string="layout_max_nf", tab_index=3, left=120, top=30, width=100, height=10)
        self.__create_control(dialog_model, type_string="FixedText", id_string="ftNameOrder", tab_index=4, left=10, top=50, width=100, height=10, value="Name order")
        name_order_cb = self.__create_control(dialog_model, type_string="CheckBox", id_string="name_order_cb", tab_index=5, left=120, top=50, width=100, height=10, value="Forename first")
        self.__create_control(dialog_model, type_string="Button", id_string="btnOk", tab_index=6, left=110, top=70, width=50, height=10, button_type=PushButtonType_OK)
        self.__create_control(dialog_model, type_string="Button", id_string="btnCancel", tab_index=7, left=170, top=70, width=50, height=10, button_type=PushButtonType_CANCEL)

        # Finally show the dialog.
        dialog = self.createUnoService("awt.UnoControlDialog")
        dialog.setModel(dialog_model)
        toolkit = self.createUnoService("awt.ExtToolkit")
        dialog.createPeer(toolkit, None)
        ret = dialog.execute()
        if ret == ExecutableDialogResults_OK:
            key = root_family_lb.StringItemList[root_family_lb.SelectedItems[0]]
            self.root_family = self.family_dict[key].fid
            self.layout_max = int(layout_max_nf.Value)
            if name_order_cb.State:
                self.node_label_image = ged2dot.Config.nodeLabelImageDefault
            else:
                self.node_label_image = ged2dot.Config.nodeLabelImageSwappedDefault
        return ret

    # XPropertyAccess
    # pylint: disable=invalid-name
    def getPropertyValues(self) -> Tuple[Any, ...]:
        try:
            return self.to_tuple(self.props)
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
            self.__extract_families()
            ret = self.__exec_dialog()
            if ret == ExecutableDialogResults_OK:
                self.props['FilterData'] = self.to_tuple({
                    'rootFamily': self.root_family,
                    'layoutMaxDepth': self.layoutMax,
                    'nodeLabelImage': self.node_label_image
                })
            return ret
        # pylint: disable=broad-except
        except Exception:
            self.printTraceback()
            return ExecutableDialogResults_CANCEL

    # XImporter
    def setTargetDocument(self, dst_doc: Any) -> None:
        self.dst_doc = dst_doc

# vim:set shiftwidth=4 softtabstop=4 expandtab:
