from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor

class ToggleSwitch(QWidget):

    toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setFixedSize(60, 30)
        self.is_on = False

    def mousePressEvent(self, event):
        self.is_on = not self.is_on
        self.toggled.emit(self.is_on)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Background
        painter.setBrush(QColor("limegreen") if self.is_on else QColor("gray"))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # Circle knob
        knob_x = 30 if self.is_on else 5
        painter.setBrush(QColor("white"))
        painter.drawEllipse(knob_x, 5, 20, 20)
    