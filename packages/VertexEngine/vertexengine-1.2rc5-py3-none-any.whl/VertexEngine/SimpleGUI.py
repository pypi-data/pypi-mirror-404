from PyQt6.QtWidgets import QPushButton, QLineEdit
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

class LegacyButton(QPushButton):
    def __init__(
        self,
        text="Button",
        width=120,
        height=40,
        text_color="white",
        border_color="#FFFFFF",
        border_width=2,
        font_name="Arial",
        font_weight=QFont.Weight.Bold,
        parent=None
    ):
        super().__init__(text, parent)
        # Store params
        self.bg_color = '#000000'
        self.hover_color = '#222222'
        self.text_color = text_color
        self.border_radius = 10
        self.border_color = border_color
        self.border_width = border_width
        self.setFont(QFont(font_name, 12, font_weight))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumSize(width, height)
        # Apply default style
        self.setStyleSheet(self.default_style())

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style())
        super().leaveEvent(event)

    def default_style(self):
        return f"""
            QPushButton {{
                background-color: {self.bg_color};
                color: {self.text_color};
                border-radius: {self.border_radius}px;
                border: {self.border_width}px solid {self.border_color};
            }}
        """
    
    def hover_style(self):
        return f"""
            QPushButton {{
                background-color: {self.hover_color};
                color: {self.text_color};
                border-radius: {self.border_radius}px;
                border: {self.border_width}px solid {self.border_color};
            }}
        """
class Text(QLabel):
    def __init__(
        self,
        text="Text",
        font_size=14,
        text_color="#FFFFFF",
        bg_color=None,
        padding=8,
        border_radius=8,
        parent=None
    ):
        super().__init__(text, parent)
        self.setFont(QFont('Arial', font_size, QFont.Weight.Normal))
        self.setAlignment(QFont.Weight.Normal)
        bg = "transparent" if bg_color is None else bg_color
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: {bg};
                padding: {padding}px;
                border-radius: {border_radius}px;
            }}
        """)

    def set_text(self, text):
        self.setText(text)

    def set_color(self, color):
        self.setStyleSheet(self.styleSheet() + f"color: {color};")

class InputField(QLineEdit):
    def __init__(
        self,
        placeholder="Enter text...",
        width=240,
        height=36,
        font_size=12,
        focus_color="#00E5FF",
        border_radius=8,
        padding=8,
        parent=None
    ):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFont(QFont('Arial', font_size))
        self.setMinimumSize(width, height)
        self.text_color = "#FFFFFF"
        self.bg_color = '#1E1E1E'
        self.border_color = '#555555'
        self.focus_color = focus_color
        self.border_radius = border_radius
        self.padding = padding
        self.apply_style(focused=False)

    def apply_style(self, focused=False):
        border = self.focus_color if focused else self.border_color
        self.setStyleSheet(f"""
            QLineEdit {{
                color: {self.text_color};
                background-color: {self.bg_color};
                border: 2px solid {border};
                border-radius: {self.border_radius}px;
                padding: {self.padding}px;
            }}
            QLineEdit::placeholder {{
                color: #888888;
            }}
        """)

    def focusInEvent(self, event):
        self.apply_style(focused=True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.apply_style(focused=False)
        super().focusOutEvent(event)

    def get_value(self):
        return self.text()
    def set_value(self, value):
        self.setText(value)