# scenes/scene.py
from .Vertex import VWidget

class Scene(VWidget):
    def __init__(self, engine):
        super().__init__(engine)  # parent = engine widget
        self.engine = engine

        # Optional: scenes can receive focus
        self.setFocusPolicy(engine.focusPolicy())

    def on_enter(self):
        """Called when the scene becomes active"""
        self.setFocus()

    def on_exit(self):
        """Called when the scene is removed"""
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

# scenes/scene_manager.py
class SceneManager:
    def __init__(self):
        self.current_scene = None

    def set_scene(self, scene):
        if self.current_scene:
            self.current_scene.on_exit()
            self.current_scene.hide()

        self.current_scene = scene
        self.current_scene.show()
        self.current_scene.on_enter()

    def update(self):
        if self.current_scene:
            self.current_scene.update()

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)
