"""WARNING: This library of Vertex is not made for games, if you want to make a game window, use the `GameEngine` Class instead."""
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QApplication
import sys
from VertexEngine import VertexUI
# ===== Base window class =====
class BaseWindow(QMainWindow):
    def __init__(self, title="Base Window", width=400, height=300):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        print(f"[DEBUG] Initialized window '{title}' with size {width}x{height}")

    def add_label(self, text):
        label = VertexUI.Text(text)
        self.layout.addWidget(label)
        print(f"[DEBUG] Added label: '{text}'")

    def add_button(self, text, callback=None):
        button = VertexUI.FancyButton(text)
        if callback:
            button.clicked.connect(callback)
        self.layout.addWidget(button)
        print(f"[DEBUG] Added button: '{text}'")

# ===== Fancy themed window =====
class FancyWindow(BaseWindow):
    def __init__(self, title="Fancy Window", width=500, height=400, theme_color="#FF69B4"):
        super().__init__(title, width, height)
        self.theme_color = theme_color
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.theme_color};
            }}
            QLabel {{
                color: white;
                font-size: 18px;
            }}
            QPushButton {{
                background-color: white;
                color: {self.theme_color};
                border-radius: 5px;
                padding: 5px 10px;
            }}
        """)
        print(f"[DEBUG] Applied theme color: {self.theme_color}")

# ===== Random fun window with auto-close button =====
class FunWindow(BaseWindow):
    def __init__(self, title="Fun Window"):
        super().__init__(title)
        self.add_label("Welcome to FunWindow! 🎉")
        self.add_button("Close me", self.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Choose your boredom mode
    window = FancyWindow(theme_color="#8A2BE2")
    window.add_label("This is super fancy 💎")
    window.add_button("Click me!", lambda: print("You clicked the fancy button!"))

    window.show()
    sys.exit(app.exec())
