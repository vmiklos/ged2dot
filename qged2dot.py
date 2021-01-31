#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""Qt-based GUI for ged2dot."""

import io
import os
import subprocess
import sys
import traceback
import webbrowser

from PyQt5 import QtGui  # type: ignore
from PyQt5.QtWidgets import QApplication  # type: ignore
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

import ged2dot


def get_abspath(path: str) -> str:
    """Make a path absolute, taking the script dir as a base dir."""
    if os.path.isabs(path):
        return path

    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


class Widgets:
    """Contains widgets which store shared state."""
    def __init__(self, window: QWidget) -> None:
        self.input_value = QLineEdit(window)
        self.output_value = QLineEdit(window)
        self.rootfamily_value = QComboBox(window)
        self.familydepth_value = QSpinBox(window)
        self.imagedir_value = QLineEdit(window)
        self.nameorder_value = QCheckBox(window)
        self.statusbar = QStatusBar()

    def set_input(self) -> None:
        """Handler for the input button."""
        try:
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
            self.update_status()
        except Exception:  # pylint: disable=broad-except
            self.print_traceback()

    def set_output(self) -> None:
        """Handler for the output button."""
        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptSave)
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
        self.update_status()

    def set_imagedir(self) -> None:
        """Handler for the imagedir button."""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        if not dialog.exec():
            return

        files = dialog.selectedFiles()
        assert len(files) == 1
        self.imagedir_value.setText(files[0])

    def convert(self) -> None:
        """Does the actual conversion."""
        try:
            config = {
                "input": self.input_value.text(),
                "output": self.output_value.text(),
                "rootfamily": self.rootfamily_value.currentData(),
                "familydepth": str(self.familydepth_value.value()),
                "imagedir": self.imagedir_value.text(),
                "nameorder": "little",
            }
            if not self.nameorder_value.isChecked():
                config["nameorder"] = "big"
            invoke_dot = False
            if self.output_value.text().endswith(".png"):
                invoke_dot = True
                config["output"] = self.output_value.text() + ".dot"
            self.statusbar.showMessage("Converting to " + config["output"] + "...")
            ged2dot.convert(config)
            if invoke_dot:
                self.statusbar.showMessage("Converting to " + self.output_value.text() + "...")
                self.to_png(config["output"], self.output_value.text())
            webbrowser.open("file://" + self.output_value.text())
            self.statusbar.showMessage("Conversion finished successfully.")
        except Exception:  # pylint: disable=broad-except
            self.print_traceback()

    @staticmethod
    def to_png(dot_path: str, png_path: str) -> None:
        """Convert the generated .dot further to .png, using dot."""
        dot_binary_path = "dot"
        if os.path.exists("/usr/local/bin/dot"):
            # Help the macOS + brew case.
            dot_binary_path = "/usr/local/bin/dot"
        elif os.path.exists(get_abspath("dot.exe")):
            # Help the Windows + bundled graphviz case.
            dot_binary_path = get_abspath("dot.exe")
        graphviz = subprocess.Popen([dot_binary_path, "-Tpng"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        assert graphviz.stdin
        with open(dot_path, "rb") as text_stream:
            graphviz.stdin.write(text_stream.read())
        graphviz.stdin.close()
        assert graphviz.stdout
        with open(png_path, "wb") as bin_stream:
            bin_stream.write(graphviz.stdout.read())
        graphviz.stdout.close()
        graphviz.wait()

    @staticmethod
    def print_traceback() -> None:
        """Shows the exception to the user when it would not be caught."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Conversion failed.")
        with io.StringIO() as stream:
            traceback.print_exc(file=stream)
            stream.seek(0)
            msg.setDetailedText(stream.read())
        msg.exec()

    def update_status(self) -> None:
        """Updates the statusbar depending on what should be the next action."""
        if not self.input_value.text():
            message = "Select an input."
        elif not self.output_value.text():
            message = "Select an output."
        else:
            message = "Press OK to start the conversion."
        self.statusbar.showMessage(message)


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

    def setup_imagedir(self) -> None:
        """Sets up the imagedir row."""
        imagedir_key = QLabel(self.window)
        imagedir_key.setText("Image directory:")
        self.grid_layout.addWidget(imagedir_key, 4, 0)
        self.grid_layout.addWidget(self.widgets.imagedir_value, 4, 1)
        imagedir_button = QPushButton(self.window)
        imagedir_button.setText("Browse...")
        imagedir_button.clicked.connect(self.widgets.set_imagedir)
        self.grid_layout.addWidget(imagedir_button, 4, 2)

    def setup_nameorder(self) -> None:
        """Sets up the nameorder row."""
        nameorder_key = QLabel(self.window)
        nameorder_key.setText("Name order:")
        self.grid_layout.addWidget(nameorder_key, 5, 0)
        self.widgets.nameorder_value.setText("Given name first")
        self.widgets.nameorder_value.setChecked(True)
        self.grid_layout.addWidget(self.widgets.nameorder_value, 5, 1)

    def exec(self) -> None:
        """Starts the main loop."""
        self.window.setWindowTitle("ged2dot")
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icon.svg")
        self.window.setWindowIcon(QtGui.QIcon(icon_path))
        self.window.setLayout(self.layout)
        self.window.show()
        sys.exit(self.qt_app.exec())


def main() -> None:
    """Commandline interface to this module."""
    app = Application()
    app.setup_input()
    app.setup_output()
    app.setup_rootfamily()
    app.setup_familydepth()
    app.setup_imagedir()
    app.setup_nameorder()

    app.layout.addLayout(app.grid_layout)

    button_box = QDialogButtonBox()
    button_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    app.layout.addWidget(button_box)
    button_box.button(QDialogButtonBox.Cancel).clicked.connect(sys.exit)
    button_box.button(QDialogButtonBox.Ok).clicked.connect(app.widgets.convert)
    app.layout.addWidget(app.widgets.statusbar)
    app.widgets.update_status()

    app.exec()


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
