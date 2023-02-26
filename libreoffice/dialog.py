#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""The dialog module provides the GedcomDialog class."""

from typing import Any
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Tuple

import unohelper  # type: ignore  # pylint: disable=import-error
from com.sun.star.beans import XPropertyAccess  # type: ignore  # pylint: disable=import-error
from com.sun.star.ui.dialogs import XExecutableDialog  # type: ignore  # pylint: disable=import-error
from com.sun.star.document import XImporter  # type: ignore  # pylint: disable=import-error
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL as ExecutableDialogResults_CANCEL  # type: ignore  # noqa: E501  # pylint: disable=import-error,line-too-long
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK as ExecutableDialogResults_OK  # noqa: E501  # pylint: disable=import-error
from com.sun.star.awt.PushButtonType import OK as PushButtonType_OK  # type: ignore  # pylint: disable=import-error
from com.sun.star.awt.PushButtonType import CANCEL as PushButtonType_CANCEL  # pylint: disable=import-error

import base
import ged2dot


class GedcomDialog(unohelper.Base, XPropertyAccess, XExecutableDialog, XImporter, base.GedcomBase):  # type: ignore
    """Provides an options dialog during import."""
    def __init__(self, context: Any, _dialogArgs: Any) -> None:
        unohelper.Base.__init__(self)
        base.GedcomBase.__init__(self, context)
        self.family_dict: Dict[str, ged2dot.Family] = {}
        self.root_family: Optional[str] = None
        self.layout_max = "4"
        self.name_order = "little"
        self.props: Dict[str, Any] = {}

    def __extract_families(self) -> None:
        ged = unohelper.fileUrlToSystemPath(self.props['URL'])
        config = {
            'input': ged,
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        self.family_dict = {}
        for node in graph:
            if not isinstance(node, ged2dot.Family):
                continue
            help_string = ""
            if node.husb and node.husb.get_surname():
                help_string += node.husb.get_surname()
            help_string += "-"
            if node.wife and node.wife.get_surname():
                help_string += node.wife.get_surname()
            key = f"{node.get_identifier()} ({help_string})"
            self.family_dict[key] = node

    def __create_control(self, options: Dict[str, Any]) -> Any:
        if "value" not in options:
            options["value"] = None
        if "button_type" not in options:
            options["button_type"] = None
        parent = options["parent"]
        control = parent.createInstance(f"com.sun.star.awt.UnoControl{options['type_string']}Model")
        control.PositionX = options["left"]
        control.PositionY = options["top"]
        control.Width = options["width"]
        control.Height = options["height"]
        control.Name = options["id_string"]
        control.TabIndex = options["tab_index"]
        if options["type_string"] == "FixedText":
            control.Label = options["value"]
        elif options["type_string"] == "Button":
            control.PushButtonType = options["button_type"]
            control.DefaultButton = options["button_type"] == PushButtonType_OK
        elif options["type_string"] == "ListBox":
            control.Dropdown = True
            # Need to check if we could make the item text and data independent to avoid parsing
            # here.
            control.StringItemList = tuple(sorted(self.family_dict.keys(), key=lambda i: int(i.split(' (')[0][1:])))
            # Select the first item.
            control.SelectedItems = tuple([0])
        elif options["type_string"] == "NumericField":
            control.Spin = True
            control.Value = 4
            control.DecimalAccuracy = 0
            control.ValueMin = 0
        elif options["type_string"] == "CheckBox":
            control.Label = options["value"]
            control.State = 1
        parent.insertByName(options["id_string"], control)
        return control

    def __exec_dialog(self) -> Any:
        # .ui files can't be used in extensions ATM, so just to have some guidelines, here are the basics:
        # 1) Control width: 50, 100, etc -- based on demand.
        # 2) Control height, padding: 10
        # The rest is just derived from this.

        # Create the dialog model.
        dialog_model = self.create_uno_service("awt.UnoControlDialogModel")
        dialog_model.PositionX = 0
        dialog_model.PositionY = 0
        dialog_model.Width = 230
        dialog_model.Height = 90
        dialog_model.Title = "GEDCOM Import"

        # Then the model of the controls.
        options = {
            "parent": dialog_model,
            "type_string": "FixedText",
            "id_string": "ftRootFamily",
            "tab_index": 0,
            "left": 10,
            "top": 10,
            "width": 100,
            "height": 10,
            "value": "Root family",
        }
        self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "ListBox",
            "id_string": "root_family_lb",
            "tab_index": 1,
            "left": 120,
            "top": 10,
            "width": 100,
            "height": 10,
        }
        root_family_lb = self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "FixedText",
            "id_string": "ftLayoutMax",
            "tab_index": 2,
            "left": 10,
            "top": 30,
            "width": 100,
            "height": 10,
            "value": "Number of generations to show",
        }
        self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "NumericField",
            "id_string": "layout_max_nf",
            "tab_index": 3,
            "left": 120,
            "top": 30,
            "width": 100,
            "height": 10,
        }
        layout_max_nf = self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "FixedText",
            "id_string": "ftNameOrder",
            "tab_index": 4,
            "left": 10,
            "top": 50,
            "width": 100,
            "height": 10,
            "value": "Name order",
        }
        self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "CheckBox",
            "id_string": "name_order_cb",
            "tab_index": 5,
            "left": 120,
            "top": 50,
            "width": 100,
            "height": 10,
            "value": "Forename first",
        }
        name_order_cb = self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "Button",
            "id_string": "btnOk",
            "tab_index": 6,
            "left": 110,
            "top": 70,
            "width": 50,
            "height": 10,
            "button_type": PushButtonType_OK,
        }
        self.__create_control(options)
        options = {
            "parent": dialog_model,
            "type_string": "Button",
            "id_string": "btnCancel",
            "tab_index": 7,
            "left": 170,
            "top": 70,
            "width": 50,
            "height": 10,
            "button_type": PushButtonType_CANCEL,
        }
        self.__create_control(options)

        # Finally show the dialog.
        dialog = self.create_uno_service("awt.UnoControlDialog")
        dialog.setModel(dialog_model)
        toolkit = self.create_uno_service("awt.ExtToolkit")
        dialog.createPeer(toolkit, None)
        ret = dialog.execute()
        if ret == ExecutableDialogResults_OK:
            key = root_family_lb.StringItemList[root_family_lb.SelectedItems[0]]
            self.root_family = self.family_dict[key].get_identifier()
            self.layout_max = layout_max_nf.Value
            if name_order_cb.State:
                self.name_order = "little"
            else:
                self.name_order = "big"
        return ret

    def getPropertyValues(self) -> Tuple[Any, ...]:  # pylint: disable=invalid-name
        """XPropertyAccess, gets the import options after showing the dialog."""
        try:
            return self.to_tuple(self.props)
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()

        return ()

    def setPropertyValues(self, props: Iterable[Any]) -> None:  # pylint: disable=invalid-name
        """XPropertyAccess, sets the import options before showing the dialog."""
        try:
            self.props = self.to_dict(props)
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()

    def setTitle(self, title: str) -> None:  # pylint: disable=invalid-name
        """XExecutableDialog, Sets the title of the dialog."""

    def execute(self) -> Any:
        """Shows the dialog that allows customizing the import options."""
        try:
            self.__extract_families()
            ret = self.__exec_dialog()
            if ret == ExecutableDialogResults_OK:
                self.props['FilterData'] = self.to_tuple({
                    'rootfamily': self.root_family,
                    'familydepth': self.layout_max,
                    'nameorder': self.name_order,
                })
            return ret
        # pylint: disable=broad-except
        except Exception:
            self.print_traceback()
            return ExecutableDialogResults_CANCEL

    def setTargetDocument(self, dst_doc: Any) -> None:  # pylint: disable=invalid-name
        """XImporter, sets the destination doc model."""

# vim:set shiftwidth=4 softtabstop=4 expandtab:
