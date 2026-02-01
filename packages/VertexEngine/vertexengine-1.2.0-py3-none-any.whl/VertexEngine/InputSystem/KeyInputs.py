from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence
KEY_MAP = {
    # Arrows
    "left": Qt.Key.Key_Left,
    "right": Qt.Key.Key_Right,
    "up": Qt.Key.Key_Up,
    "down": Qt.Key.Key_Down,

    # Actions
    "space": Qt.Key.Key_Space,
    "enter": Qt.Key.Key_Return,
    "escape": Qt.Key.Key_Escape,
    "tab": Qt.Key.Key_Tab,
    "shift": Qt.Key.Key_Shift,
    "ctrl": Qt.Key.Key_Control,
    "alt": Qt.Key.Key_Alt,
}

# Letters
for c in "abcdefghijklmnopqrstuvwxyz":
    KEY_MAP[c] = getattr(Qt.Key, f"Key_{c.upper()}")

class Input:
    _pressed = set()
    _just_pressed = set()
    _just_released = set()

    @classmethod
    def input_update(cls):
        cls._just_pressed.clear()
        cls._just_released.clear()

    @classmethod
    def key_down(cls, key):
        qt_key = KEY_MAP.get(key, key)
        if qt_key not in cls._pressed:
            cls._just_pressed.add(qt_key)
        cls._pressed.add(qt_key)

    @classmethod
    def key_up(cls, key):
        qt_key = KEY_MAP.get(key, key)
        if qt_key in cls._pressed:
            cls._just_released.add(qt_key)
        cls._pressed.discard(qt_key)

    # === Public API ===
    @classmethod
    def is_pressed(cls, key):
        return KEY_MAP[key] in cls._pressed

    @classmethod
    def is_just_pressed(cls, key):
        return KEY_MAP[key] in cls._just_pressed

    @classmethod
    def is_released(cls, key):
        return KEY_MAP[key] in cls._just_released

    class VShortcut(QShortcut):
        def __init__(self, key, parent, callback):
            super().__init__(QKeySequence(key), parent)
            self.activated.connect(callback)
