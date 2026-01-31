from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import QTimer, Qt
import pygame
from .scenes import SceneManager
from .Vertex import VWidget
pygame.init()

class GameEngine(VWidget):
    def __init__(self, width=800, height=600, fps=60):
        super().__init__()
        self.width = width
        self.height = height
        self.fps = fps

        # Qt key tracking
        self.keys_down = set()

        # pygame surface
        self.screen = pygame.Surface((self.width, self.height))

        # Scene manager
        self.scene_manager = SceneManager()

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // self.fps)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ---------------------- RENDER ----------------------

    def paintEvent(self, event):
        self.screen.fill((50, 50, 100))

        self.scene_manager.draw(self.screen)

        raw = pygame.image.tostring(self.screen, "RGBA")
        img = QImage(
            raw,
            self.width,
            self.height,
            QImage.Format.Format_RGBA8888
        )

        painter = QPainter(self)
        painter.drawImage(0, 0, img)

    def resizeEvent(self, event):
        size = event.size()
        self.width = size.width()
        self.height = size.height()
        self.screen = pygame.Surface((self.width, self.height))

    # ---------------------- UPDATE ----------------------

    def update_frame(self):
        if not self.hasFocus():
            self.keys_down.clear()

        self.scene_manager.update()
        self.update()  # triggers paintEvent

    # ---------------------- INPUT ----------------------

    def keyPressEvent(self, event):
        self.keys_down.add(event.key())

    def keyReleaseEvent(self, event):
        self.keys_down.discard(event.key())
