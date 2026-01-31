from PyQt6.QtWidgets import QListWidget

class VList(QListWidget):
    def __init__(self, items=None):
        super().__init__()

        if items:
            self.addItems(items)

    def on_click(self, callback):
        self.itemClicked.connect(callback)
        return self
