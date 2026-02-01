"""VertexEngine.Vertex: VWidget, Layouts, Dialogs, App Management"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QDialog, QLabel, QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt

# ------------------------
# Base widget wrapper
# ------------------------
class VWidget(QWidget):
    """Base widget wrapper. Handles dark mode and size; no layout by default."""

    def __init__(self, parent=None, width=None, height=None, dark_mode=False):
        super().__init__(parent)
        if width and height:
            self.setFixedSize(width, height)
        self.dark_mode = dark_mode
        if dark_mode:
            self.set_dark_mode(True)

    def set_dark_mode(self, enabled=True):
        self.dark_mode = enabled
        if enabled:
            self.setStyleSheet("""
                QWidget {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QPushButton {
                    background-color: #2980b9;
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("")


# ------------------------
# Layout wrappers
# ------------------------
class VBox(VWidget):
    """Vertical layout wrapper."""

    def __init__(self, *args, padding=10, margin=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.layout.setSpacing(padding)
        self.setLayout(self.layout)

    def add(self, widget):
        self.layout.addWidget(widget)

    def clear(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class HBox(VWidget):
    """Horizontal layout wrapper."""

    def __init__(self, *args, padding=10, margin=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.layout.setSpacing(padding)
        self.setLayout(self.layout)

    def add(self, widget):
        self.layout.addWidget(widget)

    def clear(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


# ------------------------
# Application wrapper
# ------------------------
class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

    def run(self):
        sys.exit(self.exec())


# ------------------------
# Dialog base class
# ------------------------
class Dialog(QDialog):
    def __init__(self, parent=None, title="Dialog", size=(400, 200), modal=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(*size)
        self.setModal(modal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

    def open_dialog(self):
        self.exec()

    def close_dialog(self):
        self.close()


# ------------------------
# Message dialog
# ------------------------
class MessageDialog(Dialog):
    def __init__(self, parent=None, message="", title="Message"):
        super().__init__(parent, title, (300, 150))
        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(message)
        layout.addWidget(label)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)


# ------------------------
# Confirm dialog
# ------------------------
class ConfirmDialog(Dialog):
    def __init__(self, parent=None, message="", title="Confirm"):
        super().__init__(parent, title, (350, 160))
        layout = QVBoxLayout()
        self.setLayout(layout)

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
    def ask(parent=None, message="", title="Confirm"):
        dlg = ConfirmDialog(parent, message, title)
        return dlg.exec() == QDialog.DialogCode.Accepted


# ------------------------
# Input dialog
# ------------------------
class InputDialog(Dialog):
    def __init__(self, parent=None, label="Enter:", title="Input"):
        super().__init__(parent, title, (350, 180))
        self.input = QLineEdit()

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(label))
        layout.addWidget(self.input)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

    def value(self):
        return self.input.text()

    @staticmethod
    def get(parent=None, label="Enter:", title="Input"):
        dlg = InputDialog(parent, label, title)
        if dlg.exec():
            return dlg.value()
        return None


# ------------------------
# Static dialog helper
# ------------------------
class Dialogs:
    @staticmethod
    def message(parent=None, text=""):
        MessageDialog(parent, text).open_dialog()

    @staticmethod
    def confirm(parent=None, text=""):
        return ConfirmDialog.ask(parent, text)

    @staticmethod
    def input(parent=None, text=""):
        return InputDialog.get(parent, text)


# ------------------------
# Example usage
# ------------------------
if __name__ == "__main__":
    app = App()

    main = VBox(dark_mode=True, width=500, height=400)
    main.add(QLabel("Welcome to the VWidget wrapper!"))

    btn_msg = QPushButton("Show Message")
    btn_msg.clicked.connect(lambda: Dialogs.message(main, "Hello!"))
    main.add(btn_msg)

    btn_confirm = QPushButton("Ask Confirm")
    btn_confirm.clicked.connect(lambda: print(Dialogs.confirm(main, "Are you sure?")))
    main.add(btn_confirm)

    btn_input = QPushButton("Ask Input")
    btn_input.clicked.connect(lambda: print(Dialogs.input(main, "Enter your name:")))
    main.add(btn_input)

    main.show()
    app.run()
