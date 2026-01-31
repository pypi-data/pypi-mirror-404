from PyQt6.QtWidgets import QCheckBox
class VCheckBox(QCheckBox):
    def __init__(self, text=""):
        super().__init__(text)

    def on_toggle(self, callback):
        self.stateChanged.connect(callback)
        return self
