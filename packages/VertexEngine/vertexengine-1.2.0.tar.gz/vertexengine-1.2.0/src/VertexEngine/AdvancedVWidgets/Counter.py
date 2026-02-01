from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout

class CounterWidget(QWidget):

    countChanged = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.count = 0
        self.button = QPushButton("Increase")

        self.button.clicked.connect(self.increase)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

    def increase(self):
        self.count += 1
        self.countChanged.emit(self.count)
