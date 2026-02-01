from PyQt6.QtWidgets import QComboBox

class VDropdown(QComboBox):
    def __init__(self, items=None):
        super().__init__()

        if items:
            self.addItems(items)

    def on_select(self, callback):
        self.currentTextChanged.connect(callback)
        return self
