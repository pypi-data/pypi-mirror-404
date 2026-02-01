from PyQt6.QtCore import Qt


class Mouse:
    _map = {
        "left": Qt.MouseButton.LeftButton,
        "right": Qt.MouseButton.RightButton,
        "middle": Qt.MouseButton.MiddleButton,
        "x1": Qt.MouseButton.BackButton,
        "x2": Qt.MouseButton.ForwardButton,
    }

    @staticmethod
    def resolve(btn):
        if isinstance(btn, str):
            btn = Mouse._map.get(btn.lower())
            if btn is None:
                raise KeyError(f"Unknown mouse button: {btn}")
        return btn


class MouseEvents:
    def __init__(self):
        self.current = set()
        self.last = set()

        self.on_press_events = {}
        self.on_release_events = {}
        self.on_hold_events = {}

    def update_from_qt(self, qt_buttons):
        self.current.clear()
        for btn in Mouse._map.values():
            if qt_buttons & btn:
                self.current.add(btn)

    def update(self):
        for btn in self.current - self.last:
            for f in self.on_press_events.get(btn, []):
                f()

        for btn in self.last - self.current:
            for f in self.on_release_events.get(btn, []):
                f()

        for btn in self.current:
            for f in self.on_hold_events.get(btn, []):
                f()

        self.last = self.current.copy()

    def on_press(self, btn, func):
        self.on_press_events.setdefault(Mouse.resolve(btn), []).append(func)

    def on_release(self, btn, func):
        self.on_release_events.setdefault(Mouse.resolve(btn), []).append(func)

    def on_hold(self, btn, func):
        self.on_hold_events.setdefault(Mouse.resolve(btn), []).append(func)

    def clear(self):
        self.current.clear()
        self.last.clear()
