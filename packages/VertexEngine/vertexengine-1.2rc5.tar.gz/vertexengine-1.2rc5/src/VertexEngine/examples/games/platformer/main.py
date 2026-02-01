"""
This is a simple single scene platformer, made in the Vertex Game Engine.

This  teaches you:
Basics of Asset rendering
Scenes
Game Engine
rendering to a screen
handle input
dictionaries
physics
update and drawing
"""

from VertexEngine.engine import GameEngine
from VertexEngine.scenes import Scene
from VertexEngine import VertexScreen
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
from VertexEngine.audio import AudioManager
import pygame
import os
# 🔽 WORLD SCALE
SCALE = 0.5

# 🔽 Physics (scaled)
GRAVITY = 1.2 * SCALE
JUMP_FORCE = -22 * SCALE
MOVE_SPEED = 8 * SCALE
GROUND_Y = 300 * SCALE
maindir = os.path.split(os.path.abspath(__file__))[0]
coin_img = pygame.image.load(maindir + "/data/coin.png")
coin_img = pygame.transform.scale(
    coin_img,
    (32 * SCALE, 32 * SCALE)
)

class Main(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.world_offset_y = engine.height // 2
        self.score = 0
        self.coins = [
            {"x": 200, "y": -35 * SCALE, "collected": False},
            {"x": 50,   "y": 80  * SCALE, "collected": False},
            {"x": 380,  "y": -300 * SCALE, "collected": False},
        ]
        self.platforms = [
            (200, 1 * SCALE, 200 * SCALE, 20 * SCALE),
            (360, -200 * SCALE, 200 * SCALE, 20 * SCALE),
            (0,   120 * SCALE, 220 * SCALE, 20 * SCALE),
            (350, 200 * SCALE, 180 * SCALE, 20 * SCALE),
        ]
     
        # 🔽 Player (scaled)
        self.w = int(80 * SCALE)
        self.h = int(80 * SCALE)

        self.x = 0
        self.y = 0

        self.vx = 0
        self.vy = 0
        self.on_ground = False

        self.keys = set()

    # --- INPUT ---
    def keyPressEvent(self, event):
        self.keys.add(event.key())

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    # --- UPDATE ---
    def update(self):
        self.vx = 0

        if Qt.Key.Key_A in self.keys:
            self.vx = -MOVE_SPEED
        if Qt.Key.Key_D in self.keys:
            self.vx = MOVE_SPEED

        if Qt.Key.Key_Space in self.keys and self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False

        # Gravity
        self.vy += GRAVITY

        # Apply movement
        self.x += self.vx
        self.y += self.vy

        self.on_ground = False

        for coin in self.coins:
            if coin["collected"]:
                continue
            
            cx = coin["x"]
            cy = coin["y"]
            cw = coin_img.get_width()
            ch = coin_img.get_height()

            if (
                self.x < cx + cw and
                self.x + self.w > cx and
                self.y < cy + ch and
                self.y + self.h > cy
            ):
                coin["collected"] = True
                self.score += 1
                print("Coin collected! Score:", self.score)


        # --- PLATFORM COLLISIONS ---
        for px, py, pw, ph in self.platforms:
            if (
                self.vy >= 0 and
                self.x + self.w > px and
                self.x < px + pw and
                self.y + self.h > py and
                self.y + self.h < py + ph + self.vy + 1
            ):
                self.y = py - self.h
                self.vy = 0
                self.on_ground = True

        # --- GROUND COLLISION ---
        if self.y + self.h >= GROUND_Y:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True


    # --- DRAW ---
    def draw(self, surface):
        oy = self.world_offset_y  # visual offset

        # Background
        VertexScreen.Draw.rect(
            VertexScreen.Draw,
            surface,
            (30, 30, 30),
            (0, 0, self.engine.width, self.engine.height)
        )

        # Ground (shifted DOWN)
        VertexScreen.Draw.rect(
            VertexScreen.Draw,
            surface,
            (50, 200, 50),
            (-2000 * SCALE, GROUND_Y + oy, 4000 * SCALE, 200 * SCALE)
        )

        # Player (shifted DOWN)
        VertexScreen.Draw.rect(
            VertexScreen.Draw,
            surface,
            (255, 100, 100),
            (self.x, self.y + oy, self.w, self.h)
        )

        # Coins
        for coin in self.coins:
            if coin["collected"]:
                continue
            
            surface.blit(
                coin_img,
                (coin["x"], coin["y"] + oy)
            )

        # Platforms
        for px, py, pw, ph in self.platforms:
            VertexScreen.Draw.rect(
                VertexScreen.Draw,
                surface,
                (100, 180, 255),
                (px, py + oy, pw, ph)
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)

    engine = GameEngine(
        fps=60,
        width=1920,
        height=1080,
    )

    engine.setWindowTitle("Vertex Platformer (Scaled World)")

    engine.show()

    main = Main(engine)
    engine.scene_manager.add_scene("main", main)
    engine.scene_manager.switch_to("main")

    engine.keyPressEvent = main.keyPressEvent
    engine.keyReleaseEvent = main.keyReleaseEvent

    app.exec()
