#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""Qt-based GUI for ged2dot."""

import sys

from PyQt5.QtWidgets import QApplication  # type: ignore
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget


def set_input(input_value: QLineEdit) -> None:
    """Handler for the input button."""
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setNameFilters(["GEDCOM files (*.ged)"])
    if not dialog.exec():
        return

    files = dialog.selectedFiles()
    assert len(files) == 1
    input_value.setText(files[0])


def set_output(output_value: QLineEdit) -> None:
    """Handler for the output button."""
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilters(["Graphviz files (*.dot)"])
    if not dialog.exec():
        return

    files = dialog.selectedFiles()
    assert len(files) == 1
    output_value.setText(files[0])


def main() -> None:
    """Commandline interface to this module."""
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout()
    grid_layout = QGridLayout()

    # Input
    input_key = QLabel(window)
    input_key.setText("Input:")
    grid_layout.addWidget(input_key, 0, 0)
    input_value = QLineEdit(window)
    grid_layout.addWidget(input_value, 0, 1)
    input_button = QPushButton(window)
    input_button.setText("Browse...")
    input_button.clicked.connect(lambda: set_input(input_value))
    grid_layout.addWidget(input_button, 0, 2)

    # Output
    output_key = QLabel(window)
    output_key.setText("Output:")
    grid_layout.addWidget(output_key, 1, 0)
    output_value = QLineEdit(window)
    grid_layout.addWidget(output_value, 1, 1)
    output_button = QPushButton(window)
    output_button.setText("Browse...")
    output_button.clicked.connect(lambda: set_output(output_value))
    grid_layout.addWidget(output_button, 1, 2)

    layout.addLayout(grid_layout)

    button_box = QDialogButtonBox()
    button_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(button_box)
    button_box.button(QDialogButtonBox.Cancel).clicked.connect(sys.exit)

    window.setWindowTitle("ged2dot")
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
