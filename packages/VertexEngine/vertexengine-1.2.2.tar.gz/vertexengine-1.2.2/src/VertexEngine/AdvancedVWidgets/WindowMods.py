from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem,
    QSplitter,
    QScrollArea,
    QDockWidget, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QPainter, QFont

class StarRating(QWidget):
    def __init__(self, stars=5):
        super().__init__()
        self.stars = stars
        self.rating = 0
        self.setFixedSize(150, 30)

    def mousePressEvent(self, event):
        self.rating = int(event.position().x() // 30) + 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 18))

        for i in range(self.stars):
            star = "★" if i < self.rating else "☆"
            painter.drawText(i * 30, 22, star)

class VTree(QTreeWidget):
    def __init__(self, headers=["Name"]):
        super().__init__()
        self.setHeaderLabels(headers)

    def add_item(self, text):
        item = QTreeWidgetItem([text])
        self.addTopLevelItem(item)
        return item

class VTable(QTableWidget):
    def __init__(self, rows=0, cols=0):
        super().__init__(rows, cols)

    def set_cell(self, row, col, text):
        self.setItem(row, col, QTableWidgetItem(str(text)))

class VSplitter(QSplitter):
    def __init__(self, orientation="horizontal"):
        orient = Qt.Orientation.Horizontal if orientation == "horizontal" else Qt.Orientation.Vertical
        super().__init__(orient)

    def add(self, widget):
        self.addWidget(widget)

class VScroll(QScrollArea):
    def __init__(self, widget=None):
        super().__init__()

        if widget:
            self.setWidget(widget)

        self.setWidgetResizable(True)

class VDock(QDockWidget):
    def __init__(self, title="Dock"):
        super().__init__(title)

    def set(self, widget):
        self.setWidget(widget)


class VThread(QThread):
    finished = pyqtSignal(str)

    def run(self):
        import time
        time.sleep(2)
        self.finished.emit("Thread Complete!")

class VSettings(QSettings):
    def __init__(self, organization="VertexEngine", name="App"):
        super().__init__(organization, name)

    def save(self, key, value):
        self.setValue(key, value)

    def load(self, key, default=None):
        return self.value(key, default)
