import sys
import random
import pygame

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from VertexEngine.engine import GameEngine
from VertexEngine.scenes import Scene

# =============================
# CONFIG
# =============================
WIDTH = 800
HEIGHT = 600
TILE = 30
FPS = 60
GRID_W = WIDTH // TILE
GRID_H = HEIGHT // TILE

# =============================
# SNAKE SCENE
# =============================
class SnakeScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)

        self.snake = [(10, 10)]
        self.direction = (1, 0)
        self.next_direction = self.direction

        self.food = self.spawn_food()
        self.dead = False

        self.tick = 0
        self.speed = 8  # lower = faster

    def spawn_food(self):
        return (
            random.randrange(GRID_W),
            random.randrange(GRID_H)
        )

    def set_direction(self, d):
        # Prevent instant reverse
        if (-d[0], -d[1]) != self.direction:
            self.next_direction = d

    def update(self):
        if self.dead:
            return

        self.tick += 1
        if self.tick < self.speed:
            return
        self.tick = 0

        self.direction = self.next_direction

        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Death checks
        if (
            new_head in self.snake or
            new_head[0] < 0 or new_head[1] < 0 or
            new_head[0] >= WIDTH // TILE or
            new_head[1] >= HEIGHT // TILE
        ):
            print("💀 GAME OVER")
            self.dead = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def draw(self, screen):
        screen.fill((0, 0, 0))

        for x, y in self.snake:
            pygame.draw.rect(
                screen,
                (0, 255, 0),
                (x * TILE, y * TILE, TILE, TILE)
            )

        fx, fy = self.food
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            (fx * TILE, fy * TILE, TILE, TILE)
        )

# =============================
# BOOTSTRAP (QT FIRST OR DIE)
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    engine = GameEngine(
        width=WIDTH,
        height=HEIGHT,
        fps=FPS
    )

    engine.setWindowTitle("Snake 🐍 — RC Survivor Edition")
    engine.show()

    scene = SnakeScene(engine)
    engine.scene_manager.add_scene("main", scene)
    engine.scene_manager.switch_to("main")

    # =============================
    # 🔑 QT INPUT — THIS IS THE FIX
    # =============================
    def engine_key_press(event):
        key = event.key()

        if key == Qt.Key.Key_Up:
            scene.set_direction((0, -1))
        elif key == Qt.Key.Key_Down:
            scene.set_direction((0, 1))
        elif key == Qt.Key.Key_Left:
            scene.set_direction((-1, 0))
        elif key == Qt.Key.Key_Right:
            scene.set_direction((1, 0))

    engine.keyPressEvent = engine_key_press

    app.exec()
