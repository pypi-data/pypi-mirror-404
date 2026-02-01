from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class ChatBubble(QLabel):
    def __init__(self, text, sender="me"):
        super().__init__(text)

        self.setWordWrap(True)

        if sender == "me":
            self.setStyleSheet("""
                QLabel {
                    background-color: #0078ff;
                    color: white;
                    padding: 10px;
                    border-radius: 15px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: lightgray;
                    color: black;
                    padding: 10px;
                    border-radius: 15px;
                }
            """)
