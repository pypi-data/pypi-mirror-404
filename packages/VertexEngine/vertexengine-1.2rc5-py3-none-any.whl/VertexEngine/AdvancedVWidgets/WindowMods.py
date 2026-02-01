from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem,
    QSplitter,
    QScrollArea,
    QDockWidget,
    QGraphicsView, QGraphicsScene,
)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

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
