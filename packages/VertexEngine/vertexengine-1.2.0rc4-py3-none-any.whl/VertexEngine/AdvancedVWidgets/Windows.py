from PyQt6.QtWidgets import QMessageBox, QFileDialog, QSlider, QProgressBar, QSpinBox, QToolBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
class VPopup:
    @staticmethod
    def info(text, title="Info"):
        QMessageBox.information(None, title, text)
    
    @staticmethod
    def error(text, title="Error"):
        QMessageBox.critical(None, title, text)

class VFilePicker:
    @staticmethod
    def open_file():
        file, _ = QFileDialog.getOpenFileName(None, "Open File")
        return file

    @staticmethod
    def save_file():
        file, _ = QFileDialog.getSaveFileName(None, "Save File")
        return file 

class VSlider(QSlider):
    def __init__(self, min=0, max=100):
        super().__init__(Qt.Orientation.Horizontal)

        self.setMinimum(min)
        self.setMaximum(max)

    def on_change(self, callback):
        self.valueChanged.connect(callback)
        return self

class VProgress(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setValue(0)

    def set(self, value):
        self.setValue(value)

class VSpinBox(QSpinBox):
    def __init__(self, min=0, max=100):
        super().__init__()
        self.setRange(min, max)

    def on_change(self, callback):
        self.valueChanged.connect(callback)
        return self

class VToolBar(QToolBar):
    def __init__(self, name="Toolbar"):
        super().__init__(name)

    def add_button(self, text, callback):
        action = VertexAction(text, self)
        action.triggered.connect(callback)
        self.addAction(action)

class VertexAction(QAction):
    def __init__(self, text, callback=None):
        super().__init__(text)

        if callback:
            self.triggered.connect(callback)