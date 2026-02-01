from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor

class StatusLight(QWidget):
    def __init__(self, color="red"):
        super().__init__()
        self.color = color
        self.setFixedSize(20, 20)

    def setColor(self, color):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(self.color))
        painter.drawEllipse(0, 0, 20, 20)
