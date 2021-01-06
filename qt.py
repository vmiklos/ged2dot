#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""Qt-based GUI for ged2dot."""

import sys

from PyQt5.QtWidgets import QApplication  # type: ignore
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

import ged2dot


class Widgets:
    """Contains widgets which store shared state."""
    def __init__(self, window: QWidget) -> None:
        self.input_value = QLineEdit(window)
        self.output_value = QLineEdit(window)
        self.rootfamily_value = QComboBox(window)
        self.familydepth_value = QSpinBox(window)

    def set_input(self) -> None:
        """Handler for the input button."""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters(["GEDCOM files (*.ged)"])
        if not dialog.exec():
            return

        files = dialog.selectedFiles()
        assert len(files) == 1
        ged_path = files[0]
        self.input_value.setText(ged_path)

        import_config = {
            'input': ged_path,
        }
        ged_import = ged2dot.GedcomImport()
        graph = ged_import.load(import_config)
        for node in graph:
            node.resolve(graph)
        self.rootfamily_value.clear()
        for node in graph:
            if not isinstance(node, ged2dot.Family):
                continue
            help_string = ""
            if node.husb and node.husb.get_surname():
                help_string += node.husb.get_surname()
            help_string += "-"
            if node.wife and node.wife.get_surname():
                help_string += node.wife.get_surname()
            key = "%s (%s)" % (node.get_identifier(), help_string)
            self.rootfamily_value.addItem(key, node.get_identifier())

    def set_output(self) -> None:
        """Handler for the output button."""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        name_filters = [
            "PNG files (*.png)",
            "Graphviz files (*.dot)",
        ]
        dialog.setNameFilters(name_filters)
        if not dialog.exec():
            return

        files = dialog.selectedFiles()
        assert len(files) == 1
        self.output_value.setText(files[0])


class Application:
    """Manages shared state of the app."""
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.window = QWidget()
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.widgets = Widgets(self.window)

    def setup_input(self) -> None:
        """Sets up in the input row."""
        input_key = QLabel(self.window)
        input_key.setText("Input:")
        self.grid_layout.addWidget(input_key, 0, 0)
        self.grid_layout.addWidget(self.widgets.input_value, 0, 1)
        input_button = QPushButton(self.window)
        input_button.setText("Browse...")
        input_button.clicked.connect(self.widgets.set_input)
        self.grid_layout.addWidget(input_button, 0, 2)

    def setup_output(self) -> None:
        """Sets up in the output row."""
        output_key = QLabel(self.window)
        output_key.setText("Output:")
        self.grid_layout.addWidget(output_key, 1, 0)
        self.grid_layout.addWidget(self.widgets.output_value, 1, 1)
        output_button = QPushButton(self.window)
        output_button.setText("Browse...")
        output_button.clicked.connect(self.widgets.set_output)
        self.grid_layout.addWidget(output_button, 1, 2)

    def setup_rootfamily(self) -> None:
        """Sets up the root family row."""
        rootfamily_key = QLabel(self.window)
        rootfamily_key.setText("Root family:")
        self.grid_layout.addWidget(rootfamily_key, 2, 0)
        self.grid_layout.addWidget(self.widgets.rootfamily_value, 2, 1)

    def setup_familydepth(self) -> None:
        """Sets up the familydepth row."""
        rootfamily_key = QLabel(self.window)
        rootfamily_key.setText("Family depth:")
        self.grid_layout.addWidget(rootfamily_key, 3, 0)
        self.widgets.familydepth_value.setValue(4)
        self.grid_layout.addWidget(self.widgets.familydepth_value, 3, 1)

    def exec(self) -> None:
        """Starts the main loop."""
        self.window.setWindowTitle("ged2dot")
        self.window.setLayout(self.layout)
        self.window.show()
        sys.exit(self.qt_app.exec())


def set_imagedir(imagedir_value: QLineEdit) -> None:
    """Handler for the imagedir button."""
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)
    if not dialog.exec():
        return

    files = dialog.selectedFiles()
    assert len(files) == 1
    imagedir_value.setText(files[0])


def main() -> None:
    """Commandline interface to this module."""
    app = Application()
    app.setup_input()
    app.setup_output()
    app.setup_rootfamily()
    app.setup_familydepth()

    # Image directory
    imagedir_key = QLabel(app.window)
    imagedir_key.setText("Image directory:")
    app.grid_layout.addWidget(imagedir_key, 4, 0)
    imagedir_value = QLineEdit(app.window)
    app.grid_layout.addWidget(imagedir_value, 4, 1)
    imagedir_button = QPushButton(app.window)
    imagedir_button.setText("Browse...")
    app.grid_layout.addWidget(imagedir_button, 4, 2)

    # Name order
    nameorder_key = QLabel(app.window)
    nameorder_key.setText("Name order:")
    app.grid_layout.addWidget(nameorder_key, 5, 0)
    nameorder_value = QCheckBox(app.window)
    nameorder_value.setText("Given name first")
    nameorder_value.setChecked(True)
    app.grid_layout.addWidget(nameorder_value, 5, 1)

    imagedir_button.clicked.connect(lambda: set_imagedir(imagedir_value))
    app.layout.addLayout(app.grid_layout)

    button_box = QDialogButtonBox()
    button_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    app.layout.addWidget(button_box)
    button_box.button(QDialogButtonBox.Cancel).clicked.connect(sys.exit)

    app.exec()


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
