import sys
import random
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from VertexEngine.engine import GameEngine
from VertexEngine.scenes import Scene
from VertexEngine import VertexScreen
from VertexEngine.InputSystem.KeyInputs import Input

# =====================
# CONFIG
# =====================
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 450


#class ScreenScaler:
#    def __init__(self, engine):
#        self.engine = engine
#    @property
#    def scale(self):
#        return min(
#            self.engine.width / VIRTUAL_WIDTH,
#            self.engine.height / VIRTUAL_HEIGHT,
#        )
#    @property
#    def offset_x(self):
#        return int((self.engine.width - VIRTUAL_WIDTH * self.scale) / 2)
#    @property
#    def offset_y(self):
#        return int((self.engine.height - VIRTUAL_HEIGHT * self.scale) / 2)
#    def rect(self, x, y, w, h):
#        s = self.scale
#        return (
#            int(x * s) + self.offset_x,
#            int(y * s) + self.offset_y,
#            int(w * s),
#            int(h * s),
#        )
#    def pos(self, x, y):
#        s = self.scale
#        return (
#            int(x * s) + self.offset_x,
#            int(y * s) + self.offset_y,
#        )
class ScreenScaler:
    def __init__(self, engine):
        self.engine = engine

    @property
    def scale(self):
        return min(
            self.engine.width / VIRTUAL_WIDTH,
            self.engine.height / VIRTUAL_HEIGHT,
        )
    
    # 👇 NO CENTERING
    @property
    def offset_x(self):
        return 0
    
    @property
    def offset_y(self):
        return 0
    
    def rect(self, x, y, w, h):
        s = self.scale
        return (
            int(x * s),
            int(y * s),
            int(w * s),
            int(h * s),
        )
    
    def pos(self, x, y):
        s = self.scale
        return int(x * s), int(y * s)
# =====================
# GAME OBJECTS
# =====================
class Player:
    def __init__(self):
        self.x = 230
        self.y = 300
        self.w = 40
        self.h = 40
        self.vel_y = 0
        self.on_ground = True

    def update(self):
        speed = 5

        if Input.is_pressed("a") or Input.is_pressed("left"):
            self.x -= speed
        if Input.is_pressed("d") or Input.is_pressed("right"):
            self.x += speed

        if self.x > VIRTUAL_WIDTH:
            self.x = 0
        
        if self.x < 0:
            self.x = VIRTUAL_WIDTH

        if self.on_ground and Input.is_just_pressed("space"):
            self.vel_y = -15
            self.on_ground = False

        self.vel_y += 1
        self.y += self.vel_y

        if self.y >= 300:
            self.y = 300
            self.vel_y = 0
            self.on_ground = True
        print(self.x)

class Block:
    def __init__(self):
        self.size = 40
        self.x = random.randint(0, VIRTUAL_WIDTH - self.size)
        self.y = -self.size
        self.speed = random.randint(4, 8)

    def update(self):
        self.y += self.speed


# =====================
# SCENE
# =====================
class MainScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.scaler = ScreenScaler(engine)

        self.player = Player()
        self.blocks = []
        self.dead = False

    def update(self):
        if not self.dead:
            self.player.update()

            if random.random() < 0.03:
                self.blocks.append(Block())

            for b in self.blocks:
                b.update()
                if (
                    self.player.x < b.x + b.size and
                    self.player.x + self.player.w > b.x and
                    self.player.y < b.y + b.size and
                    self.player.y + self.player.h > b.y
                ):
                    self.dead = True

            self.blocks = [b for b in self.blocks if b.y < VIRTUAL_HEIGHT]

        Input.input_update()

    def draw(self, surface):
        s = self.scaler

        # background
        VertexScreen.Draw.rect(
            VertexScreen.Draw,
            surface,
            (15, 15, 15),
            s.rect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
        )

        # player
        VertexScreen.Draw.rect(
            VertexScreen.Draw,
            surface,
            (0, 255, 255),
            s.rect(self.player.x, self.player.y, self.player.w, self.player.h),
        )

        # blocks
        for b in self.blocks:
            VertexScreen.Draw.rect(
                VertexScreen.Draw,
                surface,
                (255, 0, 0),
                s.rect(b.x, b.y, b.size, b.size),
            )

        # death text
        if self.dead:
            deathfont = VertexScreen.Font(None, 24)
            deathfont.draw(
                surface,
                "DOGPILED",
                s.pos(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2)
            )


# =====================
# ENGINE (Qt INPUT HERE)
# =====================
class DogpileEngine(GameEngine):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        Input.key_down(event.key())

    def keyReleaseEvent(self, event):
        Input.key_up(event.key())


# =====================
# RUN
# =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    engine = DogpileEngine(
        fps=60,
        width=1000,
        height=800,
    )
    engine.setWindowTitle("Dogpile Dodger (VertexEngine)")
    engine.setMinimumSize(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
    engine.show()

    scene = MainScene(engine)
    engine.scene_manager.set_scene(scene)

    sys.exit(app.exec())
