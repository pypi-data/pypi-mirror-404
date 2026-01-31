"""Manage the window. You can also create dialog boxes of different types with this Library, not recommended for games."""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, 
    QVBoxLayout, QDialog, 
    QLabel, QPushButton, QHBoxLayout,
    QHBoxLayout, QLineEdit)

class VWidget(QWidget):
    """
    Base widget class.
    """

    def __init__(self):
        super().__init__()

class HBox(VWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def add(self, widget):
        self.layout.addWidget(widget)
        
class VBox(VWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def add(self, widget):
        self.layout.addWidget(widget)

class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

    def run(self):
        sys.exit(self.exec())

class Dialog(QDialog):
    def __init__(self, parent=None, title="Dialog", size=(400, 200), modal=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(*size)
        self.setModal(modal)

    def open_dialog(self):
        self.exec()

    def close_dialog(self):
        self.close()

class MessageDialog(Dialog):
    def __init__(self, parent, message, title="Message"):
        super().__init__(parent, title, (300, 150))
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(message)
        layout.addWidget(self.label)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

class ConfirmDialog(Dialog):
    def __init__(self, parent, message, title="Confirm"):
        super().__init__(parent, title, (350, 160))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message))

        buttons = QHBoxLayout()

        yes = QPushButton("Yes")
        no = QPushButton("No")

        yes.clicked.connect(self.accept)
        no.clicked.connect(self.reject)

        buttons.addWidget(yes)
        buttons.addWidget(no)
        layout.addLayout(buttons)

    @staticmethod
    def ask(parent, message, title="Confirm"):
        dlg = ConfirmDialog(parent, message, title)
        return dlg.exec() == QDialog.DialogCode.Accepted
    
class InputDialog(Dialog):
    def __init__(self, parent, label, title="Input"):
        super().__init__(parent, title, (350, 180))

        self.input = QLineEdit()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(label))
        layout.addWidget(self.input)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

    def value(self):
        return self.input.text()

    @staticmethod
    def get(parent, label, title="Input"):
        dlg = InputDialog(parent, label, title)
        if dlg.exec():
            return dlg.value()
        return None
    
class Dialogs:
    @staticmethod
    def message(parent, text):
        MessageDialog(parent, text).open_dialog()

    @staticmethod
    def confirm(parent, text):
        return ConfirmDialog.ask(parent, text)

    @staticmethod
    def input(parent, text):
        return InputDialog.get(parent, text)
