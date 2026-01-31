from PyQt6.QtCore import QTimer, QObject, QEvent


class ButtonEvents:
    def __init__(self):
        self._timers = {}
        self._filters = {}

    def on_click(self, button, action, *args, **kwargs):
        button.clicked.connect(lambda: action(*args, **kwargs))

    def on_double_click(self, button, action, interval=250):
        timer = QTimer(button)
        timer.setSingleShot(True)
        self._timers[(button, "double")] = timer

        def handler():
            if timer.isActive():
                timer.stop()
                action()
            else:
                timer.start(interval)

        button.clicked.connect(handler)

    def on_long_press(self, button, action, duration=600):
        timer = QTimer(button)
        timer.setSingleShot(True)
        timer.timeout.connect(action)
        self._timers[(button, "long")] = timer

        button.pressed.connect(lambda: timer.start(duration))
        button.released.connect(timer.stop)

    def on_click_debounced(self, button, action, cooldown=500):
        timer = QTimer(button)
        timer.setSingleShot(True)
        self._timers[(button, "debounce")] = timer

        def handler():
            if not timer.isActive():
                action()
                timer.start(cooldown)

        button.clicked.connect(handler)

    def on_toggle(self, button, on_action, off_action=None):
        button.setCheckable(True)

        def handler(checked):
            on_action() if checked else off_action and off_action()

        button.toggled.connect(handler)

    def on_click_once(self, button, action):
        def wrapper():
            action()
            button.clicked.disconnect(wrapper)

        button.clicked.connect(wrapper)

    def on_hover(self, button, enter_action=None, leave_action=None):
        class HoverFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Enter and enter_action:
                    enter_action()
                elif event.type() == QEvent.Type.Leave and leave_action:
                    leave_action()
                return False

        filt = HoverFilter(button)
        self._filters[button] = filt
        button.installEventFilter(filt)
